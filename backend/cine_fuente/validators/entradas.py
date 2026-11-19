import re

from cine_fuente.validators.comunes import (
    error_validacion,
    validar_campos,
    validar_entero_positivo,
)
from cine_fuente.validators.reservas import validar_estado_propio


ALFABETO_CODIGO_QR = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
PATRON_CODIGO_QR = re.compile(
    rf"^[{ALFABETO_CODIGO_QR}]{{4}}-[{ALFABETO_CODIGO_QR}]{{4}}$"
)


def normalizar_codigo_qr(codigo):
    limpio = "".join(codigo.strip().upper().split())
    if "-" not in limpio and len(limpio) == 8:
        limpio = f"{limpio[:4]}-{limpio[4:]}"
    return limpio


def validar_id_entrada(entrada_id):
    return validar_entero_positivo(entrada_id, "id")


def validar_filtros_listado(parametros):
    """El filtro estado corresponde a la reserva, no a la entrada."""
    reserva_id = parametros.get("reserva_id")
    if reserva_id is not None:
        reserva_id = validar_entero_positivo(reserva_id, "reserva_id")

    return {
        "reserva_id": reserva_id,
        "estado": validar_estado_propio(parametros),
    }


def validar_body(datos):
    validar_campos(
        datos,
        {"codigo_qr"},
        {"codigo_qr"},
        error_cuerpo=("Cuerpo inválido", "Se debe enviar un objeto JSON."),
        error_desconocidos=("Cuerpo inválido", "Se debe enviar únicamente el campo codigo_qr."),
        error_faltantes=("Cuerpo inválido", "Se debe enviar únicamente el campo codigo_qr."),
    )
    codigo = datos["codigo_qr"]
    if not isinstance(codigo, str) or not codigo.strip():
        error_validacion("Código QR inválido", "codigo_qr debe ser un texto no vacío.")

    codigo_normalizado = normalizar_codigo_qr(codigo)
    if not PATRON_CODIGO_QR.fullmatch(codigo_normalizado):
        error_validacion("Código QR inválido", "codigo_qr debe tener el formato XXXX-XXXX.", "QR_FORMATO_INVALIDO")

    return codigo_normalizado
