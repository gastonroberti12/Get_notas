import pymysql

from cine_fuente.repositories.salas import (
    actualizar_sala as actualizar_sala_repo,
    consultar_sala_por_id,
    consultar_salas,
    eliminar_sala as eliminar_sala_repo,
    insertar_sala,
)
from cine_fuente.repositories.sucursales import consultar_sucursal_por_id
from cine_fuente.utils import construir_error_api


def _error(codigo, titulo, detalle, status):
    raise ValueError(construir_error_api(codigo, titulo, detalle), status)


def listar_salas(sucursal_id=None):
    return consultar_salas(sucursal_id)


def obtener_sala(sala_id):
    sala = consultar_sala_por_id(sala_id)
    if sala is None:
        _error(
            "sala.not.found",
            "Sala no encontrada",
            "La sala solicitada no existe.",
            404,
        )
    return sala


def crear_sala(sucursal_id, nombre, capacidad):
    """Crea una sala en una sucursal existente y devuelve la sala creada (409 si el nombre se repite)."""
    if consultar_sucursal_por_id(sucursal_id) is None:
        _error(
            "sucursal.not.found",
            "Sucursal no encontrada",
            "La sucursal indicada no existe.",
            404,
        )
    try:
        sala_id = insertar_sala(sucursal_id, nombre, capacidad)
    except pymysql.err.IntegrityError as causa:
        raise ValueError(construir_error_api(
            "sala.nombre.duplicado",
            "Sala duplicada",
            "Ya existe una sala con ese nombre en la sucursal.",
        ), 409) from causa

    sala = consultar_sala_por_id(sala_id)
    if sala is None:
        raise RuntimeError(
            "La sala se insertó, pero no se pudo recuperar desde la base de datos."
        )
    return sala


def modificar_sala(sala_id, cambios):
    """Modifica una sala existente (409 si el nombre se repite en la sucursal). No devuelve nada."""
    obtener_sala(sala_id)
    if "sucursal_id" in cambios and consultar_sucursal_por_id(
        cambios["sucursal_id"]
    ) is None:
        _error(
            "sucursal.not.found",
            "Sucursal no encontrada",
            "La sucursal indicada no existe.",
            404,
        )
    try:
        actualizar_sala_repo(sala_id, cambios)
    except pymysql.err.IntegrityError as causa:
        raise ValueError(construir_error_api(
            "sala.nombre.duplicado",
            "Sala duplicada",
            "Ya existe una sala con ese nombre en la sucursal.",
        ), 409) from causa


def eliminar_sala(sala_id):
    obtener_sala(sala_id)
    try:
        eliminar_sala_repo(sala_id)
    except pymysql.err.IntegrityError as causa:
        raise ValueError(construir_error_api(
            "sala.has.relaciones",
            "No se puede eliminar",
            "La sala tiene funciones o butacas relacionadas.",
        ), 409) from causa
