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
        "fecha_uso": formatear_fecha_hora(fila.get("fecha_uso")),
    }


# GET /reservas, /usuarios/me/reservas, /reservas/{id} y /reservas/{id}/entradas


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
        verificar_titular_o_admin(reserva, usuario)
    return reserva_api(reserva)


def verificar_titular_o_admin(reserva, usuario):
    """Autoriza titular o administrador."""
    if usuario.get("rol") != "administrador" and int(reserva["usuario_id"]) != int(usuario["id"]):
        error(
            "RECURSO_NO_AUTORIZADO",
            "Acceso denegado",
            "La reserva no pertenece al usuario autenticado.",
            403,
        )


def listar_entradas_reserva(reserva_id, usuario, limit, offset):
    """Lsta las entradas de la reserva para su titular o administrador."""
    procesar_expiraciones()
    reserva = compras_repo.obtener_reserva_por_id(reserva_id)
    if reserva is None:
        error("RESERVA_NO_ENCONTRADA", "Reserva no encontrada", f"No existe la reserva {reserva_id}.", 404)
    verificar_titular_o_admin(reserva, usuario)
    entradas = compras_repo.listar_entradas_reserva(reserva_id, limit, offset)
    total = compras_repo.contar_entradas_reserva(reserva_id)
    return [entrada_api(entrada) for entrada in entradas], total


# POST /reservasy /reservas/{id}/pago


def crear_reserva(usuario_id, funcion_id, butaca_ids):
    """Valida la función y las butacas, calcula el total y crea la reserva pendiente."""
    ahora = ahora_gmt3()
    ahora_db = ahora.replace(tzinfo=None)

    # Se procesan vencimientos antes de comprobar disponibilidad.
    procesar_expiraciones()

    funcion = compras_repo.obtener_funcion(funcion_id)
    if funcion is None:
        error(
            "FUNCION_NO_ENCONTRADA",
            "Función no encontrada",
            f"No existe la función {funcion_id}.",
            404,
        )

    if normalizar_fecha_local(funcion["fecha_hora"]) <= ahora:
        error(
            "FUNCION_INICIADA",
            "La función ya comenzó",
            "No se puede reservar una función que ya comenzó.",
            409,
        )

    butacas = compras_repo.obtener_butacas(butaca_ids)

    if len(butacas) != len(butaca_ids):
        encontradas = {int(butaca["id"]) for butaca in butacas}
        faltantes = sorted(set(butaca_ids) - encontradas)

        error(
            "BUTACA_NO_ENCONTRADA",
            "Butaca no encontrada",
            f"No existen las butacas: {faltantes}.",
            404,
        )

    for butaca in butacas:
        if int(butaca["sala_id"]) != int(funcion["sala_id"]):
            error(
                "BUTACA_SALA_INCORRECTA",
                "Butaca fuera de la sala de la función",
                f"La butaca {butaca['id']} no pertenece a la sala de la función seleccionada.",
                409,
            )

    # Las entradas de reservas canceladas o vencidas ya se eliminaron.
    ocupadas = compras_repo.obtener_butacas_ocupadas(funcion_id, butaca_ids)

    if ocupadas:
        error(
            "BUTACA_OCUPADA",
            "Hay butacas ocupadas",
            f"Las butacas no disponibles son: {sorted(set(ocupadas))}.",
            409,
        )

    precio = int(funcion["precio"])

    if precio <= 0:
        error(
            "PRECIO_FUNCION_INVALIDO",
            "Precio de función inválido",
            "La función no tiene un precio válido para calcular la reserva.",
            409,
        )

    reserva_id = None

    try:
        reserva_id = compras_repo.insertar_reserva({
            "usuario_id": usuario_id,
            "funcion_id": funcion_id,
            "fecha_compra": ahora_db,
            "estado": "pendiente",
            "total": precio * len(butaca_ids),
        })

        if not reserva_id:
            raise RuntimeError(
                "La base de datos no devolvió el ID de la reserva creada."
            )

        for butaca_id in butaca_ids:
            compras_repo.insertar_entrada(reserva_id, butaca_id)

        return int(reserva_id)

    except Exception:
        # Limpieza compensatoria: no equivale a una transacción real.
        if reserva_id is not None:
            try:
                compras_repo.eliminar_entradas_reserva(reserva_id)
                compras_repo.eliminar_reserva_incompleta(reserva_id)
            except Exception:
                logger.exception(
                    "No se pudo limpiar la reserva incompleta %s",
                    reserva_id,
                )

        raise