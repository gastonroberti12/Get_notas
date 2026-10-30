import os
import smtplib
from email.message import EmailMessage

from cine_fuente.services.qr_service import generar_qr_png


def enviar_confirmacion_pago(datos_reserva):
    """Envía por SMTP la confirmación de pago y los códigos QR de la reserva."""
    destinatario = datos_reserva.get("email")
    if not destinatario:
        raise ValueError("La reserva confirmada no tiene un email de destino.")

    servidor = os.getenv("SMTP_HOST")
    puerto = int(os.getenv("SMTP_PORT", "587"))
    remitente = os.getenv("SMTP_FROM")
    usuario = os.getenv("SMTP_USER")
    contrasena = os.getenv("SMTP_PASSWORD")

    if not servidor or not remitente:
        raise RuntimeError("Faltan SMTP_HOST o SMTP_FROM para enviar la confirmación.")

    mensaje = EmailMessage()
    mensaje["Subject"] = f"Confirmación de reserva #{datos_reserva['id']}"
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje.set_content(_crear_cuerpo(datos_reserva))

    for entrada in datos_reserva.get("entradas", []):
        codigo_qr = entrada.get("codigo_qr")
        if not codigo_qr:
            raise ValueError(
                f"La entrada {entrada.get('id')} no tiene un código QR asignado."
            )
        mensaje.add_attachment(
            generar_qr_png(codigo_qr),
            maintype="image",
            subtype="png",
            filename=f"entrada-{entrada['id']}.png",
        )

    with smtplib.SMTP(servidor, puerto, timeout=10) as conexion:
        conexion.starttls()
        if usuario:
            if not contrasena:
                raise RuntimeError("Falta SMTP_PASSWORD para autenticar el servidor SMTP.")
            conexion.login(usuario, contrasena)
        conexion.send_message(mensaje)


def _crear_cuerpo(datos_reserva):
    entradas = datos_reserva.get("entradas", [])
    codigos_qr = "\n".join(
        f"- Butaca {entrada['butaca_id']}: {entrada.get('codigo_qr')}"
        for entrada in entradas
    )
    return (
        f"Hola {datos_reserva.get('nombre', '')} {datos_reserva.get('apellido', '')},\n\n"
        f"Tu reserva #{datos_reserva['id']} fue confirmada.\n"
        f"Función: {datos_reserva['funcion_id']}\n"
        f"Total: {datos_reserva.get('total', 0)}\n\n"
        f"Códigos QR:\n{codigos_qr or '- No hay entradas asociadas.'}\n"
    )
