from cine_fuente.utils import construir_error_api
from cine_fuente.validators.reservas import validar_entero_positivo, validar_estado_propio


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
    if not isinstance(datos, dict):
        raise ValueError(construir_error_api(
            "ERROR_VALIDACION", "Cuerpo inválido", "Se debe enviar un objeto JSON."
        ), 400)

    if "codigo_qr" not in datos or len(datos) != 1:
        raise ValueError(construir_error_api(
            "ERROR_VALIDACION", "Cuerpo inválido",
            "Se debe enviar únicamente el campo codigo_qr."
        ), 400)

    codigo = datos["codigo_qr"]
    if not isinstance(codigo, str) or not codigo.strip() or len(codigo) > 64:
        raise ValueError(construir_error_api(
            "ERROR_VALIDACION", "Código QR inválido",
            "codigo_qr debe ser un texto no vacío de hasta 64 caracteres."
        ), 400)

    return codigo.strip()
