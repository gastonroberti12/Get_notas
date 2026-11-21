from flask import Blueprint, jsonify, request

from cine_fuente.services import salas as salas_service
from cine_fuente.services.seguridad import requiere_rol
from cine_fuente.utils import (
    respuesta_error_excepcion,
    respuesta_paginada,
    validar_paginacion,
)
from cine_fuente.validators.salas import (
    validar_creacion_sala,
    validar_modificacion_sala,
)


salas_bp = Blueprint("salas", __name__, url_prefix="/salas")


@salas_bp.route("", methods=["GET"])
def listar_salas():
    limit, offset = validar_paginacion(request.args)
    salas = salas_service.listar_salas(
        request.args.get("sucursal_id", type=int)
    )
    return respuesta_paginada(
        "salas",
        salas[offset:offset + limit],
        len(salas),
        limit,
        offset,
    )


@salas_bp.route("/<int:sala_id>", methods=["GET"])
def obtener_sala(sala_id):
    try:
        sala = salas_service.obtener_sala(sala_id)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return jsonify(sala), 200


@salas_bp.route("", methods=["POST"])
@requiere_rol("administrador")
def crear_sala():
    try:
        sucursal_id, nombre, capacidad = validar_creacion_sala(
            request.get_json(silent=True)
        )
        sala = salas_service.crear_sala(sucursal_id, nombre, capacidad)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return jsonify(sala), 201


@salas_bp.route("/<int:sala_id>", methods=["PATCH"])
@requiere_rol("administrador")
def modificar_sala(sala_id):
    try:
        cambios = validar_modificacion_sala(request.get_json(silent=True))
        salas_service.modificar_sala(sala_id, cambios)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return "", 204


@salas_bp.route("/<int:sala_id>", methods=["DELETE"])
@requiere_rol("administrador")
def borrar_sala(sala_id):
    try:
        salas_service.eliminar_sala(sala_id)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return "", 204
