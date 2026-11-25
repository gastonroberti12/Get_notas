import logging
import secrets
import base64
from datetime import timedelta, timezone


from constants import (
    RESERVA_CANCELACION_MINUTOS,
    RESERVA_EXPIRACION_MINUTOS,
    TOLERANCIA_INGRESO_MIN,
)
from cine_fuente.repositories import reservas as compras_repo
from cine_fuente.repositories.funciones_repository import consultar_funcion_por_id as obtener_funcion
from cine_fuente.repositories.butacas import obtener_butacas
from cine_fuente.utils import ahora_gmt3, construir_error_api, formatear_fecha_hora

from cine_fuente.services.notificaciones_service import (
    enviar_en_segundo_plano,
    enviar_estado_reserva,
    mail_posible,
)
from cine_fuente.services.qr_service import generar_qr_png

logger = logging.getLogger(__name__)


ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin I, O, 0 ni 1 para no confundir al tipear

def generar_codigo_ingreso():
    """Código corto para el QR y para tipear a mano. Ej: K7M2-9QXP."""
    letras = "".join(secrets.choice(ALFABETO_CODIGO) for _ in range(8))
    return f"{letras[:4]}-{letras[4:]}"


def error(code, message, description, status):
    """Lanza un ValueError con el JSON de error y el status HTTP.
    El errorhandler de app.py lo convierte en la respuesta."""
    raise ValueError(construir_error_api(code, message, description), status)


def normalizar_fecha_local(valor):
    """MySQL devuelve fechas sin zona horaria: las marca como GMT-3 (o las convierte si ya
    tenían zona) para poder compararlas con ahora_gmt3()."""
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
        "tolerancia_ingreso_min": TOLERANCIA_INGRESO_MIN,
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
    """Expira las reservas pendientes vencidas y manda el mail de aviso. Se llama antes de operar
    con reservas y además cada 30 s desde el scheduler (cine_fuente/scheduler.py)."""
    # Expira las pendientes vencidas y recorre los ids que expiró esta llamada
    for id_reserva in compras_repo.procesar_reservas_vencidas(ahora_gmt3()):
        # Si no hay mail configurado (por ejemplo, en Render), no hay nada más que hacer con esta reserva
        if not mail_posible({"email": True}):
            continue
        try:
            # Datos del cliente para el mail (email, película, butacas...)
            datos = compras_repo.obtener_datos_notificacion(id_reserva)
            if datos and mail_posible(datos):
                # Avisa "tu reserva expiró" en un hilo aparte, sin hacer esperar la respuesta
                enviar_en_segundo_plano(enviar_estado_reserva, datos)
        except Exception:
            # Un problema con el mail nunca corta el proceso: solo queda anotado en el log
            logger.exception("No se pudo preparar el mail de la reserva %s", id_reserva)


def listar_reservas(filtros, limit, offset, usuario_propio_id=None):
    """Devuelve reservas y total para paginación."""
    reservas = compras_repo.listar_reservas(filtros, limit, offset, usuario_propio_id)
    total = compras_repo.contar_reservas(filtros, usuario_propio_id)
    return [reserva_api(reserva) for reserva in reservas], total

def listar_reservas_perfil(filtros, limit, offset, usuario_id):
    """Arma las reservas del perfil con película, sala, entradas (con QR si corresponde) y servicios.
    Devuelve (lista, total)."""

    # una sola conexion a la base para todo el perfil
    reservas, total, entradas, servicios = compras_repo.obtener_datos_perfil(
        filtros, limit, offset, usuario_id
    )

    # dict reserva_id -> lista, para no recorrer todas las entradas por cada reserva
    entradas_por_reserva, servicios_por_reserva = {}, {}
    for entrada in entradas:
        entradas_por_reserva.setdefault(entrada["reserva_id"], []).append(entrada)
    for servicio in servicios:
        servicios_por_reserva.setdefault(servicio["reserva_id"], []).append(servicio)

    resultado = []

    for reserva in reservas:
        datos = reserva_api(reserva)

        datos["pelicula"] = reserva["pelicula"]
        datos["pelicula_id"] = reserva["pelicula_id"]
        datos["poster_url"] = reserva["poster_url"]
        datos["fecha_hora"] = formatear_fecha_hora(reserva["fecha_hora"])
        datos["sala"] = reserva["sala"]
        datos["sucursal"] = reserva["sucursal"]

        datos["entradas"] = []
        datos["servicios"] = []

        for entrada in entradas_por_reserva.get(reserva["id"], []):
            item = {
                "butaca": f"{entrada['fila']}{entrada['numero']}",
                "codigo_qr": entrada["codigo_qr"],
                "fecha_uso": formatear_fecha_hora(entrada["fecha_uso"])
            }
            # el QR solo se genera para entradas confirmadas y sin usar
            if (reserva["estado"] == "confirmada"
                    and entrada["codigo_qr"]
                    and entrada["fecha_uso"] is None):
                png = generar_qr_png(entrada["codigo_qr"])
                item["qr_base64"] = base64.b64encode(png).decode("ascii")
            datos["entradas"].append(item)

        for servicio in servicios_por_reserva.get(reserva["id"], []):
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
    # Sin zona horaria, porque así se guarda en MySQL.
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

    # Si trajo menos de las pedidas, alguna no existe.
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

    # El chequeo final de butacas ocupadas se hace dentro de la transacción con FOR UPDATE,
    # para que dos compras simultáneas no vendan la misma butaca.
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
    # Chequeo rápido; la garantía real está en el UPDATE de confirmar_reserva_con_qr (puede vencer entre medio).
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

    # Lista de (id_entrada, código nuevo).
    codigos_qr = [(int(entrada["id"]), generar_codigo_ingreso()) for entrada in entradas]
    # Compras anteriores a esto ya vencieron.
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
    if reserva_actualizada is None:
        raise RuntimeError("No se pudieron recuperar los datos de la reserva confirmada.")

    # El pago ya está confirmado: los datos para el mail son opcionales y nunca deben dar error 500.
    try:
        datos_notificacion = compras_repo.obtener_datos_notificacion(reserva_id)
    except Exception:
        logger.exception("No se pudieron obtener los datos de notificación de la reserva %s", reserva_id)
        datos_notificacion = None

    return reserva_api(reserva_actualizada), datos_notificacion


# PATCH /reservas/{id}

def cancelar_reserva(reserva_id, usuario):
    """Cancela la reserva si pertenece al usuario y faltan al menos 60 minutos, el estado de la misma es pendiente o confirmada"""
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
        # Solo cancela si sigue pendiente o confirmada en el momento del UPDATE.
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
    # La cancelación ya quedó guardada; si el mail falla solo se anota en el log.
    try:
        if mail_posible({"email": True}):
            datos = compras_repo.obtener_datos_notificacion(reserva_id)
            if datos and mail_posible(datos):
                enviar_en_segundo_plano(enviar_estado_reserva, datos)
    except Exception:
        logger.exception("No se pudo preparar el mail de la reserva %s", reserva_id)
