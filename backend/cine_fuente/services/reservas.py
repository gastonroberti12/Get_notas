import logging
from datetime import timedelta, timezone
from uuid import uuid4

from cine_fuente.repositories import reservas as compras_repo
from cine_fuente.utils import ahora_gmt3, construir_error_api, formatear_fecha_hora

logger = logging.getLogger(__name__)


def error(code, message, description, status):
    """Construye un error de negocio."""
    raise ValueError(construir_error_api(code, message, description), status)


def normalizar_fecha_local(valor):
    """Normaliza fechas a GMT-3 para compararlas."""
    zona_gmt3 = timezone(timedelta(hours=-3))
    if valor.tzinfo is None:
        return valor.replace(tzinfo=zona_gmt3)
    return valor.astimezone(zona_gmt3)


def reserva_api(fila):
    """Adapta una reserva al JSON."""
    return {
        "id": int(fila["id"]),
        "usuario_id": int(fila["usuario_id"]),
        "funcion_id": int(fila["funcion_id"]),
        "fecha_compra": formatear_fecha_hora(fila["fecha_compra"]),
        "estado": fila["estado"],
        "fecha_cancelacion": formatear_fecha_hora(fila.get("fecha_cancelacion")),
        "total": int(fila["total"]),
    }


def entrada_api(fila):
    """Adapta una entrada al JSON ."""
    return {
        "id": int(fila["id"]),
        "reserva_id": int(fila["reserva_id"]),
        "butaca_id": int(fila["butaca_id"]),
        "codigo_qr": fila.get("codigo_qr"),
        "estado": fila["estado"],
        "fecha_uso": formatear_fecha_hora(fila.get("fecha_uso")),
    }


# GET /reservas, /usuarios/me/reservas y /reservas/{id}


def procesar_expiraciones():
    """Procesa reservas pendientes vencidas."""
    return compras_repo.procesar_reservas_vencidas(ahora_gmt3())


def listar_reservas(filtros, limit, offset, usuario_propio_id=None):
    """Devuelve reservas y total para paginación."""
    procesar_expiraciones()
    reservas = compras_repo.listar_reservas(filtros, limit, offset, usuario_propio_id)
    total = compras_repo.contar_reservas(filtros, usuario_propio_id)
    return [reserva_api(reserva) for reserva in reservas], total


def obtener_reserva(reserva_id, usuario, exige_titular_o_admin=True):
    """Consulta una reserva y verifica titularidad o rol administrador."""
    procesar_expiraciones()
    reserva = compras_repo.obtener_reserva_por_id(reserva_id)
    if reserva is None:
        error("RESERVA_NO_ENCONTRADA", "Reserva no encontrada", f"No existe la reserva {reserva_id}.", 404)
    if exige_titular_o_admin:
        _verificar_titular_o_admin(reserva, usuario)
    return reserva_api(reserva)


def _verificar_titular_o_admin(reserva, usuario):
    """Autoriza titular o administrador."""
    if usuario.get("rol") != "administrador" and int(reserva["usuario_id"]) != int(usuario["id"]):
        error(
            "RECURSO_NO_AUTORIZADO",
            "Acceso denegado",
            "La reserva no pertenece al usuario autenticado.",
            403,
        )