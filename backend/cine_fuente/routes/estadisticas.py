from flask import Blueprint, jsonify, request

from cine_fuente.services import estadisticas as estadisticas_service
from cine_fuente.services.seguridad import requiere_rol
from cine_fuente.utils import (
    respuesta_error_excepcion,
    respuesta_error_interno,
)
from cine_fuente.validators.estadisticas import validar_filtros_estadisticas

estadisticas_bp = Blueprint("estadisticas", __name__)


# Ejecuta la validación común de filtros y delega el cálculo en el servicio.
def ejecutar(operacion):
    try:
        filtros = validar_filtros_estadisticas(request.args)
        return jsonify(operacion(filtros)), 200
    except ValueError as error:
        return respuesta_error_excepcion(error)
    except Exception as error:
        return respuesta_error_interno(error)


# GET /admin/estadisticas/ocupacion/general: devuelve la ocupación total del cine.
@estadisticas_bp.route("/admin/estadisticas/ocupacion/general", methods=["GET"])
@requiere_rol("administrador")
def get_ocupacion_general():
    return ejecutar(estadisticas_service.obtener_ocupacion_general)


# GET /admin/estadisticas/ocupacion/salas: devuelve la ocupación agrupada por sala.
@estadisticas_bp.route("/admin/estadisticas/ocupacion/salas", methods=["GET"])
@requiere_rol("administrador")
def get_ocupacion_salas():
    return ejecutar(estadisticas_service.obtener_ocupacion_salas)


# GET /admin/estadisticas/ocupacion/franjas_horarias: agrupa entradas vendidas por hora.
@estadisticas_bp.route(
    "/admin/estadisticas/ocupacion/franjas_horarias", methods=["GET"]
)
@requiere_rol("administrador")
def get_franjas_horarias():
    return ejecutar(estadisticas_service.obtener_franjas_horarias)