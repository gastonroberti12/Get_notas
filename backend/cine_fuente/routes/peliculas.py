from flask import Blueprint, jsonify, request

from cine_fuente.repositories.peliculas import (
    consultar_pelicula_por_id as obtener_pelicula,
    consultar_pelicula_por_imdb as obtener_pelicula_por_imdb,
    consultar_peliculas as listar_peliculas_locales,
    insertar_pelicula,
    actualizar_pelicula,
)
from cine_fuente.utils import (
    construir_error_api,
    requiere_token,
    respuesta_error_api,
    respuesta_paginada,
    validar_paginacion,
)
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


@peliculas_bp.post("")
@requiere_token(("administrador",))
# Permite al administrador cargar una película manualmente.
def crear_pelicula():
    datos = request.get_json(silent=True) or {}
    imdb_id = datos.get("id_externo")
    if not isinstance(imdb_id, str) or not imdb_id.strip():
        return respuesta_error_api(construir_error_api(
            "pelicula.invalid",
            "Datos de película inválidos",
            "El id_externo es obligatorio.",
        ), 400)
    if obtener_pelicula_por_imdb(imdb_id.strip()) is not None:
        return respuesta_error_api(construir_error_api(
            "pelicula.already.exists",
            "Película duplicada",
            "La película ya existe en la cartelera.",
        ), 409)

    try:
        pelicula = obtener_detalle_pelicula(imdb_id.strip())
    except OmdbResponseError as error:
        return respuesta_error_api(construir_error_api(
            "pelicula.not.found", "Película no encontrada", str(error)
        ), 404)
    except (OmdbConfigurationError, OmdbUnavailableError, OmdbError) as error:
        return respuesta_error_api(construir_error_api(
            "omdb.error", "Error de OMDb", str(error)
        ), 502)

    pelicula.update({
        "fecha_inicio_cartelera": datos.get("fecha_inicio_cartelera"),
        "fecha_fin_cartelera": datos.get("fecha_fin_cartelera"),
        "activa": True,
    })
    pelicula_id = insertar_pelicula(pelicula)
    return jsonify(obtener_pelicula(pelicula_id)), 201


@peliculas_bp.patch("/<int:pelicula_id>")
@requiere_token(("administrador",))
# Actualiza los datos editables de una película.
def modificar_pelicula(pelicula_id):
    if obtener_pelicula(pelicula_id) is None:
        return jsonify(construir_error_api(
            "pelicula.not.found", "Película no encontrada",
            "La película solicitada no existe.",
        )), 404
    datos = request.get_json(silent=True) or {}
    permitidos = (
        "titulo", "sinopsis", "poster_url", "duracion_min", "clasificacion",
        "genero", "fecha_inicio_cartelera", "fecha_fin_cartelera", "activa",
    )
    cambios = {campo: datos[campo] for campo in permitidos if campo in datos}
    if not cambios:
        return jsonify(construir_error_api(
            "invalid.body", "Datos inválidos",
            "No se enviaron campos para modificar.",
        )), 400
    actualizar_pelicula(pelicula_id, cambios)
    return "", 204


@peliculas_bp.delete("/<int:pelicula_id>")
@requiere_token(("administrador",))
# Da de baja una película sin eliminarla.
def borrar_pelicula(pelicula_id):
    if obtener_pelicula(pelicula_id) is None:
        return jsonify(construir_error_api(
            "pelicula.not.found", "Película no encontrada",
            "La película solicitada no existe.",
        )), 404
    actualizar_pelicula(pelicula_id, {"activa": False})
    return "", 204


@peliculas_bp.get("/<int:pelicula_id>")
# Obtiene una película por su identificador.
def consultar_pelicula(pelicula_id):
    pelicula = obtener_pelicula(pelicula_id)
    if pelicula is None:
        return respuesta_error_api(construir_error_api(
            "pelicula.not.found", "Película no encontrada",
            "La película solicitada no existe."
        ), 404)
    return jsonify(pelicula), 200


@peliculas_bp.get("/buscar")
# Busca películas mediante OMDb.
def buscar_peliculas():
    query = request.args.get("q", "").strip()
    if not query:
        return respuesta_error_api(construir_error_api(
            "pelicula.query.required", "Parámetro inválido",
            "El parámetro q es obligatorio."
        ), 400)
    if len(query) > 100:
        return respuesta_error_api(construir_error_api(
            "pelicula.query.max", "Parámetro inválido",
            "El parámetro q no puede superar 100 caracteres."
        ), 400)

    try:
        page = int(request.args.get("pagina", "1"))
    except ValueError:
        return respuesta_error_api(construir_error_api(
            "pelicula.page.format", "Parámetro inválido",
            "El parámetro pagina debe ser un número entero."
        ), 400)
    if not 1 <= page <= 100:
        return respuesta_error_api(construir_error_api(
            "pelicula.page.range", "Parámetro inválido",
            "El parámetro pagina debe estar entre 1 y 100."
        ), 400)

    try:
        result = buscar_peliculas_omdb(query, page)
    except OmdbConfigurationError as error:
        return respuesta_error_api(construir_error_api(
            "omdb.configuration", "Configuración de OMDb inválida", str(error)
        ), 503)
    except OmdbResponseError as error:
        return respuesta_error_api(construir_error_api(
            "omdb.response", "Respuesta inválida de OMDb", str(error)
        ), 502)
    except OmdbUnavailableError as error:
        return respuesta_error_api(construir_error_api(
            "omdb.unavailable", "OMDb no disponible", str(error)
        ), 502)

    return jsonify({"pagina": page, **result}), 200


@peliculas_bp.get("/<imdb_id>")
# Obtiene el detalle de una película externa.
def detalle_pelicula(imdb_id):
    try:
        movie = obtener_detalle_pelicula(imdb_id)
    except ValueError as error:
        return respuesta_error_api(construir_error_api(
            "pelicula.invalid", "Identificador inválido", str(error)
        ), 400)
    except OmdbConfigurationError as error:
        return respuesta_error_api(construir_error_api(
            "omdb.configuration", "Configuración de OMDb inválida", str(error)
        ), 503)
    except OmdbResponseError as error:
        return respuesta_error_api(construir_error_api(
            "pelicula.not.found", "Película no encontrada", str(error)
        ), 404)
    except OmdbUnavailableError as error:
        return respuesta_error_api(construir_error_api(
            "omdb.unavailable", "OMDb no disponible", str(error)
        ), 502)
    except OmdbError as error:
        return respuesta_error_api(construir_error_api(
            "omdb.error", "Error de OMDb", str(error)
        ), 502)

    return jsonify(movie), 200
