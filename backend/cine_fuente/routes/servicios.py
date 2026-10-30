from flask import Blueprint, jsonify, request, g

from cine_fuente.repositories.servicios import (
    consultar_servicios,
    contar_servicios,
    consultar_servicio_por_id,
    insertar_servicio,
    existe_servicio,
    actualizar_servicio,
    servicio_tiene_reservas,
    eliminar_servicio,
    consultar_servicios_reserva,
    consultar_reserva_para_servicios,
    existe_servicio_en_reserva,
    actualizar_cantidad_servicio_reserva,
    eliminar_servicio_reserva
)

from cine_fuente.validators.servicios import (
    validar_creacion_servicio,
    validar_campos_servicio,
    validar_modificacion_servicio_reserva
)

from cine_fuente.utils import (
    requiere_token,
    construir_error_api,
    validar_paginacion,
    respuesta_paginada
)


servicios_bp = Blueprint("servicios", __name__)


# AUXILIAR - Respuestas de error
def error_servicio(codigo, mensaje, estado, descripcion=None):
    return jsonify(
        construir_error_api(codigo, mensaje, descripcion or mensaje)
    ), estado


# AUXILIAR - Validar ID y existencia de servicio del catálogo
def verificar_servicio(servicio_id):

    if servicio_id <= 0:
        return error_servicio(
            "ERROR_VALIDACION", "ID inválido", 400
        )

    if not existe_servicio(servicio_id):
        return error_servicio(
            "SERVICIO_NO_ENCONTRADO", "Servicio no encontrado", 404
        )

    return None


# AUXILIAR - Comprobar quién puede acceder a los servicios de una reserva.
def verificar_reserva(reserva_id, modificar=False):
    if reserva_id <= 0:
        return error_servicio("ERROR_VALIDACION", "ID inválido", 400)

    reserva = consultar_reserva_para_servicios(reserva_id)

    if reserva is None:
        return error_servicio(
            "RESERVA_NO_ENCONTRADA", "Reserva no encontrada", 404
        )

    es_propietario = reserva["usuario_id"] == g.usuario["id"]
    es_administrador = g.usuario["rol"] == "administrador"

    # El administrador puede consultar reservas ajenas, pero solo el dueño
    # puede modificar sus servicios.
    if not es_propietario and (modificar or not es_administrador):
        return error_servicio("ACCESO_DENEGADO", "Acceso denegado", 403)

    if modificar and (reserva["estado"] != "pendiente" or not reserva["vigente"]):
        return error_servicio(
            "RESERVA_NO_MODIFICABLE",
            "Solo se pueden modificar reservas pendientes dentro de los 10 minutos",
            409
        )

    return None


# AUXILIAR - Comprobaciones compartidas por PATCH y DELETE de un servicio reservado.
def verificar_servicio_reservado(reserva_id, servicio_reserva_id):
    if servicio_reserva_id <= 0:
        return error_servicio("ERROR_VALIDACION", "ID inválido", 400)

    error = verificar_reserva(reserva_id, modificar=True)
    if error is not None:
        return error

    if not existe_servicio_en_reserva(reserva_id, servicio_reserva_id):
        return error_servicio(
            "SERVICIO_NO_ENCONTRADO", "El servicio no pertenece a la reserva", 404
        )

    return None


# 1. GET /servicios
@servicios_bp.route("/servicios", methods=["GET"])
def listar_servicios():

    try:
        limit, offset = validar_paginacion(request.args)
    except ValueError as error:
        return jsonify(error.args[0]), error.args[1]

    nombre = request.args.get("nombre")
    activo_param = request.args.get("activo")

    if activo_param is None:
        activo = None
    elif activo_param.lower() in ("true", "false"):
        activo = activo_param.lower() == "true"
    else:
        return error_servicio(
            "ERROR_VALIDACION", "Filtro activo inválido", 400
        )

    total = contar_servicios(nombre, activo)
    servicios = consultar_servicios(nombre, activo, limit, offset)

    return respuesta_paginada(
        "servicios", servicios, total, limit, offset
    )


# 2. GET /servicios/{id}
@servicios_bp.route("/servicios/<int:servicio_id>", methods=["GET"])
def obtener_servicio_por_id(servicio_id):

    if servicio_id <= 0:
        return error_servicio("ERROR_VALIDACION", "ID inválido", 400)

    servicio = consultar_servicio_por_id(servicio_id)
    if servicio is None:
        return error_servicio(
            "SERVICIO_NO_ENCONTRADO", "Servicio no encontrado", 404
        )

    return jsonify(servicio), 200


# 3. POST /servicios
@servicios_bp.route("/servicios", methods=["POST"])
@requiere_token(("administrador",))
def crear_servicio():

    try:
        campos = validar_creacion_servicio(request.get_json(silent=True))
    except ValueError as error:
        return error_servicio(
            "ERROR_VALIDACION", str(error), 400
        )

    id_creado = insertar_servicio(
        campos["nombre"], campos["descripcion"], campos["precio"], campos["activo"]
    )

    return jsonify({"id": id_creado}), 201, {
        "Location": f"/servicios/{id_creado}"
    }


# 4. PATCH /servicios/{id}
@servicios_bp.route("/servicios/<int:servicio_id>", methods=["PATCH"])
@requiere_token(("administrador",))
def modificar_servicio(servicio_id):

    error = verificar_servicio(servicio_id)
    if error is not None:
        return error

    try:
        campos = validar_campos_servicio(request.get_json(silent=True))
    except ValueError as error:
        return error_servicio(
            "ERROR_VALIDACION", str(error), 400
        )

    actualizar_servicio(servicio_id, campos)
    return "", 204


# 5. DELETE /servicios/{id}
@servicios_bp.route("/servicios/<int:servicio_id>", methods=["DELETE"])
@requiere_token(("administrador",))
def eliminar_servicio_endpoint(servicio_id):

    error = verificar_servicio(servicio_id)
    if error is not None:
        return error

    if servicio_tiene_reservas(servicio_id):
        return error_servicio(
            "SERVICIO_CON_RESERVAS",
            "El servicio tiene reservas asociadas",
            409
        )

    eliminar_servicio(servicio_id)
    return "", 204


# 6. GET /reservas/{id}/servicios
@servicios_bp.route("/reservas/<int:reserva_id>/servicios", methods=["GET"])
@requiere_token(("cliente", "administrador"))
def listar_servicios_reserva(reserva_id):

    error = verificar_reserva(reserva_id)
    if error is not None:
        return error

    servicios = consultar_servicios_reserva(reserva_id)

    if not servicios:
        return "", 204

    return jsonify({"servicios": servicios}), 200


# 7. PATCH /reservas/{id_reserva}/servicios/{id_servicio}
@servicios_bp.route(
    "/reservas/<int:reserva_id>/servicios/<int:servicio_reserva_id>",
    methods=["PATCH"]
)
@requiere_token(("cliente",))
def modificar_servicio_reserva(reserva_id, servicio_reserva_id):

    error = verificar_servicio_reservado(reserva_id, servicio_reserva_id)
    if error is not None:
        return error

    try:
        cantidad = validar_modificacion_servicio_reserva(request.get_json(silent=True))
    except ValueError as error:
        return error_servicio(
            "ERROR_VALIDACION", str(error), 400
        )

    actualizar_cantidad_servicio_reserva(
        reserva_id, servicio_reserva_id, cantidad
    )

    return "", 204


# 8. DELETE /reservas/{id_reserva}/servicios/{id_servicio}
@servicios_bp.route(
    "/reservas/<int:reserva_id>/servicios/<int:servicio_reserva_id>",
    methods=["DELETE"]
)
@requiere_token(("cliente",))
def eliminar_servicio_de_reserva(reserva_id, servicio_reserva_id):

    error = verificar_servicio_reservado(reserva_id, servicio_reserva_id)
    if error is not None:
        return error

    eliminar_servicio_reserva(reserva_id, servicio_reserva_id)

    return "", 204
