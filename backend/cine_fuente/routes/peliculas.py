from flask import Blueprint, jsonify, request

from cine_fuente.repositories.peliculas import consultar_peliculas as listar_peliculas_locales, consultar_pelicula_por_id as obtener_pelicula
from cine_fuente.utils import construir_error_api, respuesta_paginada, validar_paginacion
from cine_fuente.services.omdb_service import (
    OmdbConfigurationError,
    OmdbError,
    OmdbResponseError,
    OmdbUnavailableError,
    obtener_detalle_pelicula,
    buscar_peliculas as buscar_peliculas_omdb,
)


peliculas_bp = Blueprint("peliculas", __name__, url_prefix="/api/peliculas")


@peliculas_bp.get("")
# Lista las películas locales disponibles.
def listar_peliculas():
    limit, offset = validar_paginacion(request.args)
    peliculas = listar_peliculas_locales()
    return respuesta_paginada("peliculas", peliculas[offset:offset + limit], len(peliculas), limit, offset)


@peliculas_bp.get("/<int:pelicula_id>")
# Obtiene una película por su identificador.
def consultar_pelicula(pelicula_id):
    pelicula = obtener_pelicula(pelicula_id)
    if pelicula is None:
        return jsonify(construir_error_api("pelicula.not.found", "Película no encontrada", "La película solicitada no existe.")), 404
    return jsonify(pelicula), 200


@peliculas_bp.get("/buscar")
# Busca películas mediante OMDb.
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
        result = buscar_peliculas_omdb(query, page)
    except OmdbConfigurationError as error:
        return jsonify({"error": str(error)}), 503
    except OmdbResponseError as error:
        return jsonify({"error": str(error)}), 502
    except OmdbUnavailableError as error:
        return jsonify({"error": str(error)}), 502

    return jsonify({"pagina": page, **result}), 200


@peliculas_bp.get("/<imdb_id>")
# Obtiene el detalle de una película externa.
def detalle_pelicula(imdb_id):
    try:
        movie = obtener_detalle_pelicula(imdb_id)
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
