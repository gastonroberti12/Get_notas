from flask import Blueprint, jsonify, request

from cine_fuente.services.omdb_service import (
    OmdbConfigurationError,
    OmdbError,
    OmdbResponseError,
    OmdbUnavailableError,
    get_movie_details,
    search_movies,
)


peliculas_bp = Blueprint("peliculas", __name__, url_prefix="/api/peliculas")


@peliculas_bp.get("/buscar")
def buscar_peliculas():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "El parámetro q es obligatorio."}), 400
    if len(query) > 100:
        return jsonify({"error": "El parámetro q no puede superar 100 caracteres."}), 400

    try:
        page = int(request.args.get("pagina", "1"))
    except ValueError:
        return jsonify({"error": "El parámetro pagina debe ser un número entero."}), 400
    if not 1 <= page <= 100:
        return jsonify({"error": "El parámetro pagina debe estar entre 1 y 100."}), 400

    try:
        result = search_movies(query, page)
    except OmdbConfigurationError as error:
        return jsonify({"error": str(error)}), 503
    except OmdbResponseError as error:
        return jsonify({"error": str(error)}), 502
    except OmdbUnavailableError as error:
        return jsonify({"error": str(error)}), 502

    return jsonify({"pagina": page, **result}), 200


@peliculas_bp.get("/<imdb_id>")
def detalle_pelicula(imdb_id):
    try:
        movie = get_movie_details(imdb_id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except OmdbConfigurationError as error:
        return jsonify({"error": str(error)}), 503
    except OmdbResponseError as error:
        return jsonify({"error": str(error)}), 404
    except OmdbUnavailableError as error:
        return jsonify({"error": str(error)}), 502
    except OmdbError as error:
        return jsonify({"error": str(error)}), 502

    return jsonify(movie), 200
