from flask import Blueprint, jsonify, request
from cine_fuente.services.seguridad import requiere_rol
from cine_fuente.utils import (
    construir_error_api,
    respuesta_error_api,
    respuesta_error_excepcion,
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

from cine_fuente.services.peliculas import (
    actualizar_pelicula_por_id,
    crear_pelicula_desde_omdb,
    eliminar_pelicula,
    formatear_pelicula,
    obtener_pelicula_por_id,
    obtener_peliculas,
)

from cine_fuente.validators.peliculas import (
    parsear_fecha_cartelera,
    validar_modificacion_pelicula,
    validar_inicio_no_pasado,
    validar_rango_cartelera,
    validar_filtros,
)


peliculas_bp = Blueprint("peliculas", __name__, url_prefix="/peliculas")


@peliculas_bp.route("", methods=["GET"])
# Lista las películas locales disponibles.
def listar_peliculas():
    limit, offset = validar_paginacion(request.args)
    peliculas = obtener_peliculas(validar_filtros(request.args))
    peliculas_formateadas = [formatear_pelicula(pelicula) for pelicula in peliculas]
    return respuesta_paginada(
        "peliculas",
        peliculas_formateadas[offset:offset + limit],
        len(peliculas_formateadas),
        limit,
        offset,
    )


@peliculas_bp.route("", methods=["POST"])
@requiere_rol("administrador")
# Permite al administrador cargar una película manualmente.
def crear_pelicula():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        datos = {}
    imdb_id = datos.get("id_externo")
    if not isinstance(imdb_id, str) or not imdb_id.strip():
        return respuesta_error_api(construir_error_api(
            "pelicula.invalid",
            "Datos de película inválidos",
            "El id_externo es obligatorio.",
        ), 400)
    if "fecha_inicio_cartelera" not in datos or "fecha_fin_cartelera" not in datos:
        raise ValueError(construir_error_api(
            "pelicula.fecha.required",
            "Fechas requeridas",
            "fecha_inicio_cartelera y fecha_fin_cartelera son obligatorias.",
        ), 400)
    fecha_inicio, fecha_fin = validar_rango_cartelera(
        datos["fecha_inicio_cartelera"],
        datos["fecha_fin_cartelera"],
    )
    validar_inicio_no_pasado(parsear_fecha_cartelera(fecha_inicio, "fecha_inicio_cartelera"))

    try:
        pelicula = crear_pelicula_desde_omdb(
            imdb_id.strip(),
            fecha_inicio,
            fecha_fin,
        )
    except ValueError as error:
        return respuesta_error_excepcion(error)
    except OmdbResponseError as error:
        return respuesta_error_api(construir_error_api(
            "pelicula.not.found", "Película no encontrada", str(error)
        ), 404)
    except (OmdbConfigurationError, OmdbUnavailableError, OmdbError) as error:
        return respuesta_error_api(construir_error_api(
            "omdb.error", "Error de OMDb", str(error)
        ), 502)

    return jsonify(pelicula), 201


@peliculas_bp.route("/<int:pelicula_id>", methods=["PATCH"])
@requiere_rol("administrador")
# Actualiza los datos editables de una película.
def modificar_pelicula(pelicula_id):
    datos = request.get_json(silent=True)
    cambios = validar_modificacion_pelicula(datos)
    actualizar_pelicula_por_id(pelicula_id, cambios)
    return "", 204


@peliculas_bp.route("/<int:pelicula_id>", methods=["DELETE"])
@requiere_rol("administrador")
# Da de baja una película sin eliminarla.
def borrar_pelicula(pelicula_id):
    try:
        eliminar_pelicula(pelicula_id)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return "", 204


@peliculas_bp.route("/<int:pelicula_id>", methods=["GET"])
# Obtiene una película por su identificador.
def consultar_pelicula(pelicula_id):
    pelicula = obtener_pelicula_por_id(pelicula_id)
    if pelicula is None:
        return respuesta_error_api(construir_error_api(
            "pelicula.not.found", "Película no encontrada",
            "La película solicitada no existe."
        ), 404)
    return jsonify(pelicula), 200


@peliculas_bp.route("/buscar", methods=["GET"])
@requiere_rol("administrador")
def buscar_peliculas():
    """Busca películas mediante OMDb."""
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


@peliculas_bp.route("/<imdb_id>", methods=["GET"])
@requiere_rol("administrador")
def detalle_pelicula(imdb_id):
    """Obtiene el detalle de una película externa."""
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
