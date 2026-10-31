
from flask import Blueprint, g, jsonify, request
from cine_fuente.services.seguridad import requiere_rol
from cine_fuente.services import entradas as entradas_service

from cine_fuente.validators.entradas import (
    validar_filtros_listado,
    validar_id_entrada,
)

from cine_fuente.utils import (
    respuesta_error_excepcion,
    respuesta_error_interno,
    respuesta_paginada,
    validar_paginacion,
)


entradas_bp = Blueprint("entradas", __name__)


# GET /entradas: listado para el administrador, con filtros y paginación.
@entradas_bp.route("/entradas", methods=["GET"])
@requiere_rol("administrador")
def get_entradas():
    try:
        filtros = validar_filtros_listado(request.args)
        limit, offset = validar_paginacion(request.args)
        entradas, total = entradas_service.listar_entradas(filtros, limit, offset)
        return respuesta_paginada("entradas", entradas, total, limit, offset)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    except Exception as error:
        return respuesta_error_interno(error)


# GET /entradas/{id}: solo el administrador o el dueño de la reserva.
@entradas_bp.route("/entradas/<int:entrada_id>", methods=["GET"])
@requiere_rol("cliente", "administrador")
def get_entrada_id(entrada_id):
    try:
        entrada_id = validar_id_entrada(entrada_id)
        entrada = entradas_service.obtener_entrada(entrada_id, g.usuario)
        return jsonify(entrada), 200
    except ValueError as error:
        return respuesta_error_excepcion(error)
    except Exception as error:
        return respuesta_error_interno(error)
