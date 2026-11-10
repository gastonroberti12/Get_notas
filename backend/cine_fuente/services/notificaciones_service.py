import os
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path
from markupsafe import Markup
import logging, threading, time
logger = logging.getLogger(__name__)

from jinja2 import Environment, FileSystemLoader, select_autoescape
from constants import RESERVA_CANCELACION_MINUTOS
from cine_fuente.services.qr_service import generar_qr_png

DIR_BASE = Path(__file__).resolve().parent.parent
DIR_TEMPLATES = DIR_BASE / "templates" / "email"
DIR_CSS = DIR_BASE / "static" / "css"
_entorno = Environment(loader=FileSystemLoader(DIR_TEMPLATES), autoescape=select_autoescape())


def _items(d):
    """Lista de (nombre, cantidad, precio_unitario) con entradas y servicios."""
    items = [("Entradas", len(d.get("entradas", [])), d["precio_entrada"])]
    return items + [(s["nombre"], s["cantidad"], s["precio_unitario"]) for s in d.get("servicios", [])]


def _fecha(d):
    return d["fecha_hora"].strftime("%d/%m/%Y a las %H:%M hs")


def _butaca(e):
    return f"{e['fila']}{e['numero']}"


def _url_cancelacion(d):
    base = os.getenv("FRONTEND_URL")
    return f"{base}/reservas/{d['id']}/cancelar" if base else None


def _crear_texto(d):
    """Versión texto plano (fallback para clientes sin HTML)."""
    items = "\n".join(f"{c} x {n}: ${c * p}" for n, c, p in _items(d))
    butacas = ", ".join(_butaca(e) for e in d["entradas"])
    url = _url_cancelacion(d)
    cancelar = f"\nPodés cancelar hasta {RESERVA_CANCELACION_MINUTOS} min antes de la función: {url}\n" if url else ""
    codigos = "\n".join(f"{_butaca(e)}: {e['codigo_qr']}" for e in d["entradas"])
    return (
        f"Hola {d['nombre']},\n\nTu reserva #{d['id']} fue confirmada.\n\n"
        f"Película: {d['pelicula']}\nFecha: {_fecha(d)}\n"
        f"Lugar: {d['sucursal']} - {d['sala']}\nButacas: {butacas}\n\n"
        f"Códigos de ingreso:\n{codigos}\n\n"
        f"{items}\nTotal: ${d['total']}\n{cancelar}\n"
        "Presentá los QR adjuntos (o el código) al ingresar a la sala."
    )


def _crear_html(d, cids):
    """Renderiza el template del mail con su CSS embebido en el <head>."""
    css = (DIR_CSS / "confirmacion.css").read_text(encoding="utf-8")
    return _entorno.get_template("confirmacion.html").render(
        d=d, cids=cids, items=_items(d), fecha=_fecha(d), url=_url_cancelacion(d),
        minutos=RESERVA_CANCELACION_MINUTOS,
        estilos=Markup(f"<style>{css}</style>"),
    )

def enviar_confirmacion_pago(datos_reserva):
    """Envía por SMTP la confirmación de pago con los QR embebidos y adjuntos."""
    destinatario = datos_reserva.get("email")
    if not destinatario:
        raise ValueError("La reserva confirmada no tiene un email de destino.")

    entradas = datos_reserva.get("entradas", [])
    if any(not e.get("codigo_qr") for e in entradas):
        raise ValueError("Hay entradas sin código QR asignado.")
    pngs = [generar_qr_png(e["codigo_qr"]) for e in entradas]
    cids = [make_msgid(domain="cineparadiso.local") for _ in entradas]

    mensaje = EmailMessage()
    mensaje["Subject"] = f"Entradas confirmadas: {datos_reserva['pelicula']} - Reserva #{datos_reserva['id']}"
    mensaje["To"] = destinatario
    mensaje.set_content(_crear_texto(datos_reserva))
    mensaje.add_alternative(_crear_html(datos_reserva, cids), subtype="html")

    html = mensaje.get_body(preferencelist=("html",))
    for png, cid in zip(pngs, cids):
        html.add_related(png, maintype="image", subtype="png", cid=cid)
    for e, png in zip(entradas, pngs):
        mensaje.add_attachment(png, maintype="image", subtype="png",
                               filename=f"entrada-butaca-{_butaca(e)}.png")

    _enviar_smtp(mensaje)

def _enviar_smtp(mensaje):
    servidor, remitente = os.getenv("SMTP_HOST"), os.getenv("SMTP_FROM")
    if not servidor or not remitente:
        raise RuntimeError("Faltan SMTP_HOST o SMTP_FROM.")
    mensaje["From"] = remitente
    usuario, contrasena = os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD")
    with smtplib.SMTP(servidor, int(os.getenv("SMTP_PORT", "587")), timeout=10) as conexion:
        conexion.starttls()
        if usuario:
            if not contrasena:
                raise RuntimeError("Falta SMTP_PASSWORD.")
            conexion.login(usuario, contrasena)
        conexion.send_message(mensaje)

def mail_posible(datos):
    """Chequeo barato y síncrono: hay destinatario y SMTP configurado."""
    return bool(datos.get("email") and os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM"))

def enviar_en_segundo_plano(funcion_envio, datos, intentos=3, espera=2):
    """Lanza el envío en un hilo, con reintentos y resultado en el log."""
    def tarea():
        for n in range(1, intentos + 1):
            try:
                funcion_envio(datos)
                logger.info("Mail enviado (reserva %s, intento %s)", datos["id"], n)
                return
            except Exception:
                logger.exception("Falló el mail de la reserva %s (intento %s)", datos["id"], n)
                time.sleep(espera * n)
        logger.error("Mail NO enviado tras %s intentos (reserva %s)", intentos, datos["id"])
    threading.Thread(target=tarea, daemon=True).start()

def enviar_estado_reserva(d):
    """Mail de cancelación o expiración, según d['estado']."""
    expirada = d["estado"] == "expirada"
    titulo = "Tu reserva expiró" if expirada else "Tu reserva fue cancelada"
    detalle = ("No se registró el pago a tiempo y las butacas fueron liberadas."
               if expirada else "Las butacas fueron liberadas.")
    mensaje = EmailMessage()
    mensaje["Subject"] = f"{titulo} - Reserva #{d['id']}"
    mensaje["To"] = d["email"]
    mensaje.set_content(f"Hola {d['nombre']},\n\n{titulo}.\n{detalle}\n\n"
                        f"Película: {d['pelicula']}\nFecha: {_fecha(d)}\n"
                        f"Lugar: {d['sucursal']} - {d['sala']}")
    mensaje.add_alternative(_entorno.get_template("estado_reserva.html").render(
        d=d, titulo=titulo, detalle=detalle, fecha=_fecha(d),
        estilos=Markup(f"<style>{(DIR_CSS / 'confirmacion.css').read_text(encoding='utf-8')}</style>"),
    ), subtype="html")
    _enviar_smtp(mensaje)