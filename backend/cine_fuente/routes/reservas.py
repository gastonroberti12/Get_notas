import logging

from flask import Blueprint, g, jsonify, make_response, request

from cine_fuente.services import compras_service
from cine_fuente.services.notificaciones_service import enviar_confirmacion_pago
from cine_fuente.utils import (
    construir_error_api,
    requiere_token,
    respuesta_paginada,
    validar_paginacion,
)
from cine_fuente.validators.compra import (
    validar_body_cancelar_reserva,
    validar_body_crear_reserva,
    validar_filtros_listado,
    validar_id_reserva,
    validar_estado_propio,
)

logger = logging.getLogger(__name__)
reservas_bp = Blueprint("reservas", __name__)


def respuesta_error_excepcion(error: ValueError):
    """Convierte errores de validación o negocio en el formato JSON."""
    payload = error.args[0] if error.args and isinstance(error.args[0], dict) else construir_error_api(
        "ERROR_VALIDACION", "Solicitud inválida", "Los datos enviados no son válidos."
    )
    status = error.args[1] if len(error.args) > 1 and isinstance(error.args[1], int) else 400
    return jsonify(payload), status


def respuesta_error_interno():
    """Responde errores no esperados de los endpoints de reservas sin filtrar detalles de la BD."""
    logger.exception("Error interno en el módulo de Reservas")
    return jsonify(construir_error_api(
        "ERROR_INTERNO", "Error interno del servidor", "No se pudo completar la operación solicitada."
    )), 500


# Endpoint GET /reservas
@reservas_bp.route("/reservas", methods=["GET"])
@requiere_token(("administrador",))
def get_reservas():
    try:
        filtros = validar_filtros_listado(request.args)
        limit, offset = validar_paginacion(request.args)
        reservas, total = compras_service.listar_reservas(filtros, limit, offset)
        return respuesta_paginada("reservas", reservas, total, limit, offset)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    except Exception:
        return respuesta_error_interno()


# Endpoint GET /usuarios/me/reservas: devuelve solo las reservas del usuario autenticado.
@reservas_bp.route("/usuarios/me/reservas", methods=["GET"])
@requiere_token()
def get_mis_reservas():
    try:
        estado = validar_estado_propio(request.args)
        limit, offset = validar_paginacion(request.args)
        filtros = {"usuario_id": None, "funcion_id": None, "estado": estado, "fecha_desde": None, "fecha_hasta": None}
        reservas, total = compras_service.listar_reservas(
            filtros, limit, offset, usuario_propio_id=int(g.usuario["id"])
        )
        return respuesta_paginada("reservas", reservas, total, limit, offset)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    except Exception:
        return respuesta_error_interno()


# Endpoint GET /reservas/{id}: devuelve una reserva solo al titular o al administrador.
@reservas_bp.route("/reservas/<int:id_reserva>", methods=["GET"])
@requiere_token()
def get_reserva_id(id_reserva):
    try:
        id_valido = validar_id_reserva(id_reserva)
        reserva = compras_service.obtener_reserva(id_valido, g.usuario)
        return jsonify(reserva), 200
    except ValueError as error:
        return respuesta_error_excepcion(error)
    except Exception:
        return respuesta_error_interno()