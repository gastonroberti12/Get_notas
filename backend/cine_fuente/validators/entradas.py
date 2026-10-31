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
