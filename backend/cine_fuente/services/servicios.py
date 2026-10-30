from cine_fuente.repositories.servicios import (
    existe_servicio,
    consultar_reserva_para_servicios,
    existe_servicio_en_reserva
)

from cine_fuente.utils import construir_error_api


# Verificar existencia de un servicio del catálogo
def verificar_servicio(servicio_id):

    if servicio_id <= 0:
        return construir_error_api(
            "ERROR_VALIDACION",
            "ID inválido",
            "El ID del servicio debe ser mayor a cero"
        ), 400

    if not existe_servicio(servicio_id):
        return construir_error_api(
            "SERVICIO_NO_ENCONTRADO",
            "Servicio no encontrado",
            "No existe un servicio con ese ID"
        ), 404

    return None


# Verificar acceso y estado de una reserva
def verificar_reserva(reserva_id, usuario, modificar=False):

    if reserva_id <= 0:
        return construir_error_api(
            "ERROR_VALIDACION",
            "ID inválido",
            "El ID de la reserva debe ser mayor a cero"
        ), 400

    reserva = consultar_reserva_para_servicios(reserva_id)

    if reserva is None:
        return construir_error_api(
            "RESERVA_NO_ENCONTRADA",
            "Reserva no encontrada",
            "No existe una reserva con ese ID"
        ), 404

    es_propietario = reserva["usuario_id"] == usuario["id"]
    es_administrador = usuario["rol"] == "administrador"

    if not es_propietario and (modificar or not es_administrador):
        return construir_error_api(
            "ACCESO_DENEGADO",
            "Acceso denegado",
            "No tiene permisos para acceder a esta reserva"
        ), 403

    if modificar and (
        reserva["estado"] != "pendiente"
        or not reserva["vigente"]
    ):
        return construir_error_api(
            "RESERVA_NO_MODIFICABLE",
            "Reserva no modificable",
            "Solo se pueden modificar reservas pendientes dentro de los 10 minutos"
        ), 409
    return None


# Verificar que un servicio reservado pertenezca a la reserva
def verificar_servicio_reservado(reserva_id, servicio_reserva_id, usuario):

    if servicio_reserva_id <= 0:
        return construir_error_api(
            "ERROR_VALIDACION",
            "ID inválido",
            "El ID del servicio reservado debe ser mayor a cero"
        ), 400

    error = verificar_reserva(reserva_id, usuario, modificar=True)

    if error is not None:
        return error

    if not existe_servicio_en_reserva(reserva_id, servicio_reserva_id):
        return construir_error_api(
            "SERVICIO_NO_ENCONTRADO",
            "Servicio no encontrado",
            "El servicio no pertenece a la reserva indicada"
        ), 404
    return None
