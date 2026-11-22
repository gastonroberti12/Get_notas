from cine_fuente.repositories import servicios as servicios_repo
from constants import RESERVA_EXPIRACION_MINUTOS

from cine_fuente.utils import construir_error_api


# Verificar existencia de un servicio del catálogo
def verificar_servicio(servicio_id):

    if servicio_id <= 0:
        return construir_error_api(
            "ERROR_VALIDACION",
            "ID inválido",
            "El ID del servicio debe ser mayor a cero"
        ), 400

    if not servicios_repo.existe_servicio(servicio_id):
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

    reserva = servicios_repo.consultar_reserva_para_servicios(reserva_id)

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
            f"Solo se pueden modificar reservas pendientes dentro de los {RESERVA_EXPIRACION_MINUTOS} minutos"
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

    if not servicios_repo.existe_servicio_en_reserva(
        reserva_id, servicio_reserva_id
    ):
        return construir_error_api(
            "SERVICIO_NO_ENCONTRADO",
            "Servicio no encontrado",
            "El servicio no pertenece a la reserva indicada"
        ), 404
    return None


def _elevar_fallo(fallo):
    if fallo is not None:
        raise ValueError(fallo[0], fallo[1])


def listar_servicios(nombre, activo, limit, offset):
    total = servicios_repo.contar_servicios(nombre, activo)
    servicios = servicios_repo.consultar_servicios(
        nombre, activo, limit, offset
    )
    return servicios, total


def obtener_servicio(servicio_id):
    _elevar_fallo(verificar_servicio(servicio_id))
    servicio = servicios_repo.consultar_servicio_por_id(servicio_id)
    if servicio is None:
        raise ValueError(construir_error_api(
            "SERVICIO_NO_ENCONTRADO",
            "Servicio no encontrado",
            "Servicio no encontrado",
        ), 404)
    return servicio


def crear_servicio(campos):
    return servicios_repo.insertar_servicio(
        campos["nombre"],
        campos["descripcion"],
        campos["precio"],
        campos["activo"],
    )


def modificar_servicio(servicio_id, campos):
    _elevar_fallo(verificar_servicio(servicio_id))
    servicios_repo.actualizar_servicio(servicio_id, campos)


def eliminar_servicio(servicio_id):
    _elevar_fallo(verificar_servicio(servicio_id))
    if servicios_repo.servicio_tiene_reservas(servicio_id):
        raise ValueError(construir_error_api(
            "SERVICIO_CON_RESERVAS",
            "El servicio tiene reservas asociadas",
            "El servicio tiene reservas asociadas",
        ), 409)
    servicios_repo.eliminar_servicio(servicio_id)


def agregar_servicio_a_reserva(
    reserva_id, usuario, servicio_id, cantidad
):
    _elevar_fallo(verificar_reserva(reserva_id, usuario, modificar=True))
    _elevar_fallo(verificar_servicio(servicio_id))
    if servicios_repo.insertar_servicio_reserva(
        reserva_id, servicio_id, cantidad
    ) == 0:
        raise ValueError(construir_error_api(
            "SERVICIO_INACTIVO",
            "El servicio seleccionado no está activo",
            "El servicio seleccionado no está activo",
        ), 409)


def listar_servicios_de_reserva(reserva_id, usuario):
    _elevar_fallo(verificar_reserva(reserva_id, usuario))
    return servicios_repo.consultar_servicios_reserva(reserva_id)


def modificar_cantidad_servicio_reserva(
    reserva_id, servicio_reserva_id, usuario, cantidad
):
    _elevar_fallo(verificar_servicio_reservado(
        reserva_id, servicio_reserva_id, usuario
    ))
    servicios_repo.actualizar_cantidad_servicio_reserva(
        reserva_id, servicio_reserva_id, cantidad
    )


def eliminar_servicio_de_reserva(
    reserva_id, servicio_reserva_id, usuario
):
    _elevar_fallo(verificar_servicio_reservado(
        reserva_id, servicio_reserva_id, usuario
    ))
    servicios_repo.eliminar_servicio_reserva(
        reserva_id, servicio_reserva_id
    )
