from flask import Blueprint, g, jsonify, request

from cine_fuente.services import servicios as servicios_service
from cine_fuente.services.seguridad import requiere_rol
from cine_fuente.utils import (
    respuesta_error_excepcion,
    respuesta_paginada,
    validar_paginacion,
)
from cine_fuente.validators.comunes import validar_booleano_query
from cine_fuente.validators.servicios import (
    validar_agregado_servicio_reserva,
    validar_campos_servicio,
    validar_creacion_servicio,
    validar_modificacion_servicio_reserva,
)


servicios_bp = Blueprint("servicios", __name__)


@servicios_bp.route("/servicios", methods=["GET"])
def listar_servicios():
    limit, offset = validar_paginacion(request.args)
    nombre = request.args.get("nombre")
    activo = validar_booleano_query(
        request.args,
        "activo",
        "ERROR_VALIDACION",
        "Filtro activo inválido",
        "Filtro activo inválido",
    )
    servicios, total = servicios_service.listar_servicios(
        nombre, activo, limit, offset
    )
    return respuesta_paginada("servicios", servicios, total, limit, offset)


@servicios_bp.route("/servicios/<int:servicio_id>", methods=["GET"])
def obtener_servicio_por_id(servicio_id):
    try:
        servicio = servicios_service.obtener_servicio(servicio_id)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return jsonify(servicio), 200


@servicios_bp.route("/servicios", methods=["POST"])
@requiere_rol("administrador")
def crear_servicio():
    try:
        campos = validar_creacion_servicio(request.get_json(silent=True))
        id_creado = servicios_service.crear_servicio(campos)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return jsonify({"id": id_creado}), 201, {
        "Location": f"/servicios/{id_creado}",
    }


@servicios_bp.route("/servicios/<int:servicio_id>", methods=["PATCH"])
@requiere_rol("administrador")
def modificar_servicio(servicio_id):
    try:
        campos = validar_campos_servicio(request.get_json(silent=True))
        servicios_service.modificar_servicio(servicio_id, campos)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return "", 204


@servicios_bp.route("/servicios/<int:servicio_id>", methods=["DELETE"])
@requiere_rol("administrador")
def eliminar_servicio_endpoint(servicio_id):
    try:
        servicios_service.eliminar_servicio(servicio_id)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return "", 204


@servicios_bp.route("/reservas/<int:reserva_id>/servicios", methods=["POST"])
@requiere_rol("cliente")
def agregar_servicio_reserva(reserva_id):
    try:
        servicio_id, cantidad = validar_agregado_servicio_reserva(
            request.get_json(silent=True)
        )
        servicios_service.agregar_servicio_a_reserva(
            reserva_id,
            g.usuario,
            servicio_id,
            cantidad,
        )
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return "", 201


@servicios_bp.route("/reservas/<int:reserva_id>/servicios", methods=["GET"])
@requiere_rol("cliente", "administrador")
def listar_servicios_reserva(reserva_id):
    try:
        servicios = servicios_service.listar_servicios_de_reserva(
            reserva_id, g.usuario
        )
    except ValueError as error:
        return respuesta_error_excepcion(error)
    if not servicios:
        return "", 204
    return jsonify({"servicios": servicios}), 200


@servicios_bp.route(
    "/reservas/<int:reserva_id>/servicios/<int:servicio_reserva_id>",
    methods=["PATCH"],
)
@requiere_rol("cliente")
def modificar_servicio_reserva(reserva_id, servicio_reserva_id):
    try:
        cantidad = validar_modificacion_servicio_reserva(
            request.get_json(silent=True)
        )
        servicios_service.modificar_cantidad_servicio_reserva(
            reserva_id,
            servicio_reserva_id,
            g.usuario,
            cantidad,
        )
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return "", 204


@servicios_bp.route(
    "/reservas/<int:reserva_id>/servicios/<int:servicio_reserva_id>",
    methods=["DELETE"],
)
@requiere_rol("cliente")
def eliminar_servicio_de_reserva(reserva_id, servicio_reserva_id):
    try:
        servicios_service.eliminar_servicio_de_reserva(
            reserva_id,
            servicio_reserva_id,
            g.usuario,
        )
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return "", 204
