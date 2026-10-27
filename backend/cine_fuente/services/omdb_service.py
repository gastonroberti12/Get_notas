import os
import re

import requests


OMDB_URL = "https://www.omdbapi.com/"
REQUEST_TIMEOUT_SECONDS = 8
IMDB_ID_PATTERN = re.compile(r"^tt\d+$")
RUNTIME_PATTERN = re.compile(r"^(\d+)\s+min$")


class OmdbError(Exception):
    pass


class OmdbConfigurationError(OmdbError):
    pass


class OmdbUnavailableError(OmdbError):
    pass


class OmdbResponseError(OmdbError):
    pass


def _request_omdb(params):
    api_key = os.getenv("OMDB_API_KEY", "").strip()
    if not api_key:
        raise OmdbConfigurationError("Falta configurar la variable OMDB_API_KEY.")

    try:
        response = requests.get(
            OMDB_URL,
            params={"apikey": api_key, **params},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise OmdbUnavailableError("No se pudo conectar con OMDb.") from error

    try:
        data = response.json()
    except ValueError as error:
        raise OmdbUnavailableError("OMDb devolvió una respuesta inválida.") from error

    if not isinstance(data, dict):
        raise OmdbUnavailableError("OMDb devolvió una respuesta inválida.")
    return data


def _check_api_response(data):
    if data.get("Response") == "False":
        message = data.get("Error", "OMDb no pudo completar la consulta.")
        if message == "Invalid API key!":
            raise OmdbConfigurationError("La clave configurada para OMDb no es válida.")
        raise OmdbResponseError(message)


def _optional_value(value):
    if not isinstance(value, str) or value == "N/A":
        return None
    return value


def _to_movie_summary(item):
    return {
        "id_externo": item.get("imdbID"),
        "titulo": item.get("Title"),
        "anio": item.get("Year"),
        "tipo": item.get("Type"),
        "poster_url": _optional_value(item.get("Poster")),
    }


def search_movies(query, page=1):
    data = _request_omdb({"s": query, "type": "movie", "page": page})
    if data.get("Response") == "False" and data.get("Error") == "Movie not found!":
        return {"resultados": [], "total_resultados": 0}
    _check_api_response(data)

    results = data.get("Search", [])
    if not isinstance(results, list):
        raise OmdbUnavailableError("OMDb devolvió una lista de películas inválida.")

    try:
        total_results = int(data.get("totalResults", 0))
    except (TypeError, ValueError):
        raise OmdbUnavailableError("OMDb devolvió un total de resultados inválido.")

    return {
        "resultados": [_to_movie_summary(item) for item in results if isinstance(item, dict)],
        "total_resultados": total_results,
    }


def get_movie_details(imdb_id):
    if not IMDB_ID_PATTERN.fullmatch(imdb_id):
        raise ValueError("El identificador debe tener el formato tt seguido de números.")

    data = _request_omdb({"i": imdb_id, "plot": "full"})
    _check_api_response(data)

    runtime = _optional_value(data.get("Runtime"))
    runtime_match = RUNTIME_PATTERN.fullmatch(runtime or "")
    return {
        "id_externo": data.get("imdbID"),
        "titulo": data.get("Title"),
        "anio": data.get("Year"),
        "sinopsis": _optional_value(data.get("Plot")),
        "poster_url": _optional_value(data.get("Poster")),
        "duracion_min": int(runtime_match.group(1)) if runtime_match else None,
        "clasificacion": _optional_value(data.get("Rated")),
        "genero": _optional_value(data.get("Genre")),
    }
