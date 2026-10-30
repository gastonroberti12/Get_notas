from cine_fuente.repositories import servicios as servicios_repo
from cine_fuente.utils import construir_error_api


def verificar_servicio(servicio_id):
    if not servicios_repo.existe_servicio(servicio_id):
        return (
            construir_error_api(
                "SERVICIO_NO_ENCONTRADO",
                "Servicio no encontrado",
                "El servicio solicitado no existe.",
            ),
            404,
        )
    return None


def verificar_reserva(reserva_id, usuario):
    reserva = servicios_repo.consultar_reserva_para_servicios(reserva_id)
    if reserva is None:
        return (
            construir_error_api(
                "RESERVA_NO_ENCONTRADA",
                "Reserva no encontrada",
                "La reserva solicitada no existe.",
            ),
            404,
        )

    if usuario.get("rol") != "administrador" and reserva["usuario_id"] != usuario.get("id"):
        return (
            construir_error_api(
                "RESERVA_NO_AUTORIZADA",
                "Acceso denegado",
                "La reserva pertenece a otro usuario.",
            ),
            403,
        )

    return None


def verificar_servicio_reservado(reserva_id, servicio_reserva_id, usuario):
    error = verificar_reserva(reserva_id, usuario)
    if error is not None:
        return error

    if not servicios_repo.existe_servicio_en_reserva(
        reserva_id, servicio_reserva_id
    ):
        return (
            construir_error_api(
                "SERVICIO_RESERVADO_NO_ENCONTRADO",
                "Servicio reservado no encontrado",
                "El servicio no pertenece a la reserva indicada.",
            ),
            404,
        )

    return None
