import os  # Módulo para interactuar con el sistema operativo
import re  # Módulo para trabajar con expresiones regulares (Regular Expressions)

import requests

# URL base para realizar las peticiones a la API de OMDb
OMDB_URL = "https://www.omdbapi.com/"
# Tiempo máximo de espera (en segundos) para evitar que las peticiones queden colgadas
REQUEST_TIMEOUT_SECONDS = 8
# Expresión regular para validar el formato de un ID de IMDb (ej: "tt0133093")
IMDB_ID_PATTERN = re.compile(r"^tt\d+$")
# Expresión regular para extraer la cantidad numérica de minutos en la duración (ej: "136 min" -> 136)
RUNTIME_PATTERN = re.compile(r"^(\d+)\s+min$")

# --- JERARQUÍA DE EXCEPCIONES PERSONALIZADAS ---

class OmdbError(Exception):
    """Excepción base para todos los errores relacionados con el módulo OMDb."""
    pass

class OmdbConfigurationError(OmdbError):
    """Se lanza cuando faltan variables de entorno o la API Key no es válida."""
    pass

class OmdbUnavailableError(OmdbError):
    """Se lanza cuando hay fallos de red, timeouts o respuestas corruptas de OMDb."""
    pass

class OmdbResponseError(OmdbError):
    """Se lanza cuando la API responde correctamente pero devuelve un error de negocio (ej: 'Movie not found!')."""
    pass

# Realiza una consulta a OMDb.
def solicitar_omdb(params):
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


# Comprueba si OMDb respondió con un error.
def verificar_respuesta_api(data):
    if data.get("Response") == "False":
        message = data.get("Error", "OMDb no pudo completar la consulta.")
        if message == "Invalid API key!":
            raise OmdbConfigurationError("La clave configurada para OMDb no es válida.")
        raise OmdbResponseError(message)


def valor_opcional(value):
    if not isinstance(value, str) or value == "N/A":
        return None
    return value


def resumen_pelicula(item):
    return {
        "id_externo": item.get("imdbID"),
        "titulo": item.get("Title"),
        "anio": item.get("Year"),
        "tipo": item.get("Type"),
        "poster_url": valor_opcional(item.get("Poster")),
    }


# Busca películas mediante OMDb.
def buscar_peliculas(query, page=1):
    data = solicitar_omdb({"s": query, "type": "movie", "page": page})
    error = data.get("Error", "").strip() if isinstance(data.get("Error"), str) else ""
    if data.get("Response") == "False" and error == "Pelicula no encontrada!":
        return {"resultados": [], "total_resultados": 0}
    verificar_respuesta_api(data)

    results = data.get("Search", [])
    if not isinstance(results, list):
        raise OmdbUnavailableError("OMDb devolvió una lista de películas inválida.")

    try:
        total_results = int(data.get("totalResults", 0))
    except (TypeError, ValueError):
        raise OmdbUnavailableError("OMDb devolvió un total de resultados inválido.")

    return {
        "resultados": [resumen_pelicula(item) for item in results if isinstance(item, dict)],
        "total_resultados": total_results,
    }


# Obtiene el detalle normalizado de una película.
def obtener_detalle_pelicula(imdb_id):
    if not IMDB_ID_PATTERN.fullmatch(imdb_id):
        raise ValueError("El identificador debe tener el formato tt seguido de números.")

    data = solicitar_omdb({"i": imdb_id, "plot": "full"})
    verificar_respuesta_api(data)

    runtime = valor_opcional(data.get("Runtime"))
    runtime_match = RUNTIME_PATTERN.fullmatch(runtime or "")
    return {
        "id_externo": data.get("imdbID"),
        "titulo": data.get("Title"),
        "anio": data.get("Year"),
        "sinopsis": valor_opcional(data.get("Plot")),
        "poster_url": valor_opcional(data.get("Poster")),
        "duracion_min": int(runtime_match.group(1)) if runtime_match else None,
        "clasificacion": valor_opcional(data.get("Rated")),
        "genero": valor_opcional(data.get("Genre")),
    }
