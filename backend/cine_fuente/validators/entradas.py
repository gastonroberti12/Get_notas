from cine_fuente.validators.comunes import (
    error_validacion,
    validar_campos,
    validar_entero_positivo,
    validar_texto,
)
from cine_fuente.validators.reservas import validar_estado_propio


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
    if not isinstance(codigo, str) or not codigo.strip() or len(codigo) > 64:
        error_validacion("Código QR inválido", "codigo_qr debe ser un texto no vacío de hasta 64 caracteres.")
    return validar_texto(codigo, "codigo_qr", 64)