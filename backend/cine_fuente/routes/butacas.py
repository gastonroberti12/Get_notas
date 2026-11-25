from flask import Blueprint, jsonify, request

from cine_fuente.services import butacas as butacas_service
from cine_fuente.services.seguridad import requiere_rol
from cine_fuente.utils import (
    respuesta_error_excepcion,
    respuesta_paginada,
    validar_paginacion,
)
from cine_fuente.validators.butacas import (
    validar_creacion_butaca,
    validar_modificacion_butaca,
)


butacas_bp = Blueprint("butacas", __name__)


@butacas_bp.route("/salas/<int:sala_id>/butacas", methods=["GET"])
def listar_butacas_sala(sala_id):
    limit, offset = validar_paginacion(request.args)
    try:
        butacas = butacas_service.listar_butacas_sala(sala_id)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return respuesta_paginada(
        "butacas",
        butacas[offset:offset + limit],
        len(butacas),
        limit,
        offset,
    )


@butacas_bp.route("/salas/<int:sala_id>/butacas/generar", methods=["POST"])
@requiere_rol("administrador")
def generar_butacas(sala_id):
    try:
        cantidad = butacas_service.generar_butacas_sala(sala_id)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return jsonify({"mensaje": "Butacas generadas", "cantidad": cantidad}), 201


@butacas_bp.route("/butacas", methods=["POST"])
@requiere_rol("administrador")
def crear_butaca():
    try:
        sala_id, fila, numero = validar_creacion_butaca(
            request.get_json(silent=True)
        )
        butaca = butacas_service.crear_butaca(sala_id, fila, numero)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return jsonify(butaca), 201


@butacas_bp.route("/butacas/<int:butaca_id>", methods=["PATCH"])
@requiere_rol("administrador")
def modificar_butaca(butaca_id):
    try:
        cambios = validar_modificacion_butaca(request.get_json(silent=True))
        butacas_service.modificar_butaca(butaca_id, cambios)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return "", 204


@butacas_bp.route("/butacas/<int:butaca_id>", methods=["DELETE"])
@requiere_rol("administrador")
def borrar_butaca(butaca_id):
    try:
        butacas_service.eliminar_butaca(butaca_id)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return "", 204


@butacas_bp.route("/salas/<int:sala_id>/butacas", methods=["DELETE"])
@requiere_rol("administrador")
def borrar_butacas_sala(sala_id):
    try:
        butacas_service.eliminar_butacas_sala(sala_id)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    return "", 204
