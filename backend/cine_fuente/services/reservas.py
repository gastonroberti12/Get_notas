import logging
import secrets

from datetime import timedelta, timezone
from uuid import uuid4

from constants import RESERVA_CANCELACION_MINUTOS, RESERVA_EXPIRACION_MINUTOS
from cine_fuente.repositories import reservas as compras_repo
from cine_fuente.repositories.funciones_repository import consultar_funcion_por_id as obtener_funcion
from cine_fuente.repositories.butacas import obtener_butacas
from cine_fuente.utils import ahora_gmt3, construir_error_api, formatear_fecha_hora

from cine_fuente.services.notificaciones_service import (
    enviar_en_segundo_plano,
    enviar_estado_reserva,
    mail_posible,
)

logger = logging.getLogger(__name__)


ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin I, O, 0 ni 1 para no confundir al tipear

def generar_codigo_ingreso():
    """Código corto para el QR y para tipear a mano. Ej: K7M2-9QXP."""
    letras = "".join(secrets.choice(ALFABETO_CODIGO) for _ in range(8))
    return f"{letras[:4]}-{letras[4:]}"


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
    fecha_compra = fila["fecha_compra"]
    return {
        "id": int(fila["id"]),
        "usuario_id": int(fila["usuario_id"]),
        "funcion_id": int(fila["funcion_id"]),
        "fecha_compra": formatear_fecha_hora(fecha_compra),
        "fecha_expiracion": formatear_fecha_hora(
            fecha_compra + timedelta(minutes=RESERVA_EXPIRACION_MINUTOS)
        ),
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
    for id_reserva in compras_repo.procesar_reservas_vencidas(ahora_gmt3()):
        datos = compras_repo.obtener_datos_notificacion(id_reserva)
        if datos and mail_posible(datos):
            enviar_en_segundo_plano(enviar_estado_reserva, datos)


def listar_reservas(filtros, limit, offset, usuario_propio_id=None):
    """Devuelve reservas y total para paginación."""
    reservas = compras_repo.listar_reservas(filtros, limit, offset, usuario_propio_id)
    total = compras_repo.contar_reservas(filtros, usuario_propio_id)
    return [reserva_api(reserva) for reserva in reservas], total

#obtiene las reservas del usuario con todos sus detalles
def listar_reservas_perfil(filtros, limit, offset, usuario_id):


    #obtenemos las reservas
    reservas = compras_repo.listar_reservas_perfil(
        filtros, limit, offset, usuario_id
    )

    total = compras_repo.contar_reservas(filtros, usuario_id)

    reserva_ids = [reserva["id"] for reserva in reservas]

    #consultamos entradas y servicios
    entradas = compras_repo.listar_entradas_perfil(reserva_ids)
    servicios = compras_repo.listar_servicios_perfil(reserva_ids)

    resultado = []

    for reserva in reservas:
        datos = reserva_api(reserva)

        datos["pelicula"] = reserva["pelicula"]
        datos["poster_url"] = reserva["poster_url"]
        datos["fecha_hora"] = formatear_fecha_hora(reserva["fecha_hora"])
        datos["sala"] = reserva["sala"]
        datos["sucursal"] = reserva["sucursal"]

        datos["entradas"] = []
        datos["servicios"] = []

        # asociamos las entradas
        for entrada in entradas:
            if entrada["reserva_id"] == reserva["id"]:
                datos["entradas"].append({
                    "butaca": f"{entrada['fila']}{entrada['numero']}",
                    "fecha_uso": formatear_fecha_hora(entrada["fecha_uso"])
                })

        # asociamos los servicios que corresponden
        for servicio in servicios:
            if servicio["reserva_id"] == reserva["id"]:
                datos["servicios"].append({
                    "nombre": servicio["nombre"],
                    "cantidad": servicio["cantidad"]
                })

        resultado.append(datos)

    return resultado, total


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
    """Lista las entradas de la reserva para su titular o administrador."""
    reserva = compras_repo.obtener_reserva_por_id(reserva_id)
    if reserva is None:
        error("RESERVA_NO_ENCONTRADA", "Reserva no encontrada", f"No existe la reserva {reserva_id}.", 404)
    verificar_titular_o_admin(reserva, usuario)
    entradas = compras_repo.listar_entradas_reserva(reserva_id, limit, offset)
    total = compras_repo.contar_entradas_reserva(reserva_id)
    return [entrada_api(entrada) for entrada in entradas], total


# POST /reservas y /reservas/{id}/pago


def crear_reserva(usuario_id, funcion_id, butaca_ids):
    """Valida la función y las butacas y crea la reserva pendiente."""
    ahora = ahora_gmt3()
    ahora_db = ahora.replace(tzinfo=None)

    # Se procesan vencimientos antes de comprobar disponibilidad.
    procesar_expiraciones()

    funcion = obtener_funcion(funcion_id)
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

    if "activa" in funcion and not funcion["activa"]:
        error(
            "FUNCION_INACTIVA",
            "Función inactiva",
            "No se puede reservar una función inactiva.",
            409,
        )

    butacas = obtener_butacas(butaca_ids)

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

    if funcion["precio"] <= 0:
        error("PRECIO_FUNCION_INVALIDO", "Precio de función inválido",
              "La función no tiene un precio válido para calcular la reserva.", 409)

    reserva_id, ocupadas = compras_repo.crear_reserva_con_entradas(
        {"usuario_id": usuario_id, "funcion_id": funcion_id,
         "fecha_compra": ahora_db, "estado": "pendiente"},
        butaca_ids,
    )
    if ocupadas:
        error("BUTACA_OCUPADA", "Hay butacas ocupadas",
              f"Las butacas no disponibles son: {ocupadas}.", 409)
    return reserva_id


def confirmar_pago(reserva_id, usuario):
    """Simula el pago, confirma la reserva y asigna QR a sus entradas."""
    ahora = ahora_gmt3()
    procesar_expiraciones()
    reserva = compras_repo.obtener_reserva_por_id(reserva_id)
    if reserva is None:
        error("RESERVA_NO_ENCONTRADA", "Reserva no encontrada", f"No existe la reserva {reserva_id}.", 404)
    if int(reserva["usuario_id"]) != int(usuario["id"]):
        error("RECURSO_NO_AUTORIZADO", "Acceso denegado", "Solo el titular puede pagar la reserva.", 403)
    if reserva["estado"] != "pendiente":
        error(
            "RESERVA_NO_PENDIENTE",
            "No se puede pagar la reserva",
            "La reserva debe estar pendiente y dentro del plazo de pago.",
            409,
        )

    entradas = compras_repo.obtener_entradas_para_pago(reserva_id)
    if not entradas:
        error(
            "RESERVA_SIN_ENTRADAS",
            "La reserva no tiene entradas",
            "No se puede confirmar una reserva sin entradas asociadas.",
            409,
        )

    codigos_qr = [(int(entrada["id"]), str(uuid4())) for entrada in entradas]
    fecha_limite = (
        ahora - timedelta(minutes=RESERVA_EXPIRACION_MINUTOS)
    ).replace(tzinfo=None)
    actualizada = compras_repo.confirmar_reserva_con_qr(
        reserva_id, codigos_qr, fecha_limite
    )
    if actualizada != 1:
        error(
            "RESERVA_NO_PENDIENTE",
            "No se puede pagar la reserva",
            "La reserva debe estar pendiente y dentro del plazo de pago.",
            409,
        )

    reserva_actualizada = compras_repo.obtener_reserva_por_id(reserva_id)
    datos_notificacion = compras_repo.obtener_datos_notificacion(reserva_id)
    if reserva_actualizada is None or datos_notificacion is None:
        raise RuntimeError("No se pudieron recuperar los datos de la reserva confirmada.")

    return reserva_api(reserva_actualizada), datos_notificacion


# PATCH /reservas/{id}

def cancelar_reserva(reserva_id, usuario):
    """Cancela la reserva si pertenece al usuario y faltan al menos 60 minutos."""
    ahora = ahora_gmt3()
    procesar_expiraciones()
    reserva = compras_repo.obtener_reserva_por_id(reserva_id)
    if reserva is None:
        error("RESERVA_NO_ENCONTRADA", "Reserva no encontrada", f"No existe la reserva {reserva_id}.", 404)
    verificar_titular_o_admin(reserva, usuario)

    estado_anterior = reserva["estado"]
    if estado_anterior not in ("pendiente", "confirmada"):
        error(
            "RESERVA_NO_CANCELABLE",
            "Reserva no cancelable",
            "Solo se pueden cancelar reservas pendientes o confirmadas.",
            409,
        )

    fecha_funcion = compras_repo.obtener_fecha_funcion_de_reserva(reserva_id)
    if fecha_funcion is None:
        error("FUNCION_NO_ENCONTRADA", "Función no encontrada", "La función asociada a la reserva no existe.", 404)
    if normalizar_fecha_local(fecha_funcion) - ahora < timedelta(minutes=RESERVA_CANCELACION_MINUTOS):
        error(
            "PLAZO_CANCELACION_VENCIDO",
            "No se puede cancelar la reserva",
            "La cancelación requiere al menos una hora de anticipación.",
            409,
        )

    actualizadas = compras_repo.actualizar_estado_reserva(
        reserva_id,
        "cancelada",
        fecha_cancelacion=ahora.replace(tzinfo=None),
        estados_esperados=("pendiente", "confirmada"),
    )
    if actualizadas != 1:
        error(
            "RESERVA_NO_CANCELABLE",
            "Reserva no cancelable",
            "La reserva ya no está pendiente o confirmada.",
            409,
        )

    datos = compras_repo.obtener_datos_notificacion(reserva_id)
    if datos and mail_posible(datos):
        enviar_en_segundo_plano(enviar_estado_reserva, datos)

