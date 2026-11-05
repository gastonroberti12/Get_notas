from datetime import datetime

from flask import Blueprint, jsonify, request
from cine_fuente.services.seguridad import requiere_rol
from cine_fuente.repositories.peliculas import (
    consultar_pelicula_por_id as obtener_pelicula,
    consultar_pelicula_por_imdb as obtener_pelicula_por_imdb,
    insertar_pelicula,
    actualizar_pelicula,
)
from cine_fuente.utils import (
    construir_error_api,
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

from cine_fuente.services.peliculas_service import (
    dar_de_baja,
    formatear_pelicula,
    obtener_peliculas,
)

from cine_fuente.validators.peliculas import (
    convertir_fecha_existente,
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
    datos = request.get_json(silent=True) or {}
    imdb_id = datos.get("id_externo")
    if not isinstance(imdb_id, str) or not imdb_id.strip():
        return respuesta_error_api(construir_error_api(
            "pelicula.invalid",
            "Datos de película inválidos",
            "El id_externo es obligatorio.",
        ), 400)
    pelicula_existente = obtener_pelicula_por_imdb(imdb_id.strip())
    if pelicula_existente is not None:
        mensaje = (
            "La película ya existe pero está dada de baja; "
            "reactivala desde el listado."
            if not pelicula_existente["activa"]
            else "La película ya existe en la cartelera."
        )
        return respuesta_error_api(construir_error_api(
            "pelicula.already.exists",
            "Película duplicada",
            mensaje,
        ), 409)

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
        "fecha_inicio_cartelera": datetime.fromisoformat(fecha_inicio).replace(tzinfo=None),
        "fecha_fin_cartelera": datetime.fromisoformat(fecha_fin).replace(tzinfo=None),
        "activa": True,
    })
    pelicula_id = insertar_pelicula(pelicula)
    return jsonify(formatear_pelicula(obtener_pelicula(pelicula_id))), 201


@peliculas_bp.route("/<int:pelicula_id>", methods=["PATCH"])
@requiere_rol("administrador")
# Actualiza los datos editables de una película.
def modificar_pelicula(pelicula_id):
    pelicula_actual = obtener_pelicula(pelicula_id)
    if pelicula_actual is None:
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
    if "fecha_inicio_cartelera" in cambios or "fecha_fin_cartelera" in cambios:
        fecha_inicio = convertir_fecha_existente(
            cambios.get("fecha_inicio_cartelera", pelicula_actual["fecha_inicio_cartelera"])
        )
        fecha_fin = convertir_fecha_existente(
            cambios.get("fecha_fin_cartelera", pelicula_actual["fecha_fin_cartelera"])
        )
        if fecha_inicio is not None or fecha_fin is not None:
            if fecha_inicio is None or fecha_fin is None:
                raise ValueError(construir_error_api(
                    "pelicula.fecha.required",
                    "Fechas requeridas",
                    "La película debe tener fecha de inicio y fecha de fin.",
                ), 400)
            validar_rango_cartelera(fecha_inicio, fecha_fin)
    if cambios.get("activa") is False:
        if not dar_de_baja(pelicula_id):
            return respuesta_error_api(construir_error_api(
                "BAJA_CON_RESERVAS_ACTIVAS",
                "No se puede dar de baja la película",
                "La película tiene reservas activas para funciones futuras.",
            ), 409)
        cambios.pop("activa")
    if cambios:
        actualizar_pelicula(pelicula_id, cambios)
    return "", 204


@peliculas_bp.route("/<int:pelicula_id>", methods=["DELETE"])
@requiere_rol("administrador")
# Da de baja una película sin eliminarla.
def borrar_pelicula(pelicula_id):
    if obtener_pelicula(pelicula_id) is None:
        return jsonify(construir_error_api(
            "pelicula.not.found", "Película no encontrada",
            "La película solicitada no existe.",
        )), 404
    if not dar_de_baja(pelicula_id):
        return respuesta_error_api(construir_error_api(
            "BAJA_CON_RESERVAS_ACTIVAS",
            "No se puede dar de baja la película",
            "La película tiene reservas activas para funciones futuras.",
        ), 409)
    return "", 204


@peliculas_bp.route("/<int:pelicula_id>", methods=["GET"])
# Obtiene una película por su identificador.
def consultar_pelicula(pelicula_id):
    pelicula = obtener_pelicula(pelicula_id)
    if pelicula is None:
        return respuesta_error_api(construir_error_api(
            "pelicula.not.found", "Película no encontrada",
            "La película solicitada no existe."
        ), 404)
    return jsonify(formatear_pelicula(pelicula)), 200


@peliculas_bp.route("/buscar", methods=["GET"])
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


@peliculas_bp.route("/<imdb_id>", methods=["GET"])
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
