import pymysql

from cine_fuente.repositories.butacas import (
    actualizar_butaca as actualizar_butaca_repo,
    consultar_butaca_por_id,
    consultar_butacas_por_sala,
    eliminar_butaca as eliminar_butaca_repo,
    eliminar_butacas_de_sala as eliminar_butacas_de_sala_repo,
    generar_butacas_atomico,
    insertar_butaca,
)
from cine_fuente.repositories.salas import consultar_sala_por_id
from cine_fuente.utils import construir_error_api


def _exigir_sala(sala_id):
    if consultar_sala_por_id(sala_id) is None:
        raise ValueError(construir_error_api(
            "sala.not.found",
            "Sala no encontrada",
            "La sala solicitada no existe.",
        ), 404)


def _exigir_butaca(butaca_id):
    butaca = consultar_butaca_por_id(butaca_id)
    if butaca is None:
        raise ValueError(construir_error_api(
            "butaca.not.found",
            "Butaca no encontrada",
            "La butaca solicitada no existe.",
        ), 404)
    return butaca


def listar_butacas_sala(sala_id):
    _exigir_sala(sala_id)
    return consultar_butacas_por_sala(sala_id)


def generar_butacas_sala(sala_id):
    return generar_butacas_atomico(sala_id)


def crear_butaca(sala_id, fila, numero):
    _exigir_sala(sala_id)
    try:
        butaca_id = insertar_butaca(sala_id, fila, numero)
    except pymysql.err.IntegrityError as causa:
        raise ValueError(construir_error_api(
            "butaca.duplicada",
            "Butaca duplicada",
            "La fila y el número ya existen en la sala.",
        ), 409) from causa

    butaca = consultar_butaca_por_id(butaca_id)
    if butaca is None:
        raise RuntimeError(
            "La butaca se insertó, pero no se pudo recuperar desde la base de datos."
        )
    return butaca


def modificar_butaca(butaca_id, cambios):
    _exigir_butaca(butaca_id)
    try:
        actualizar_butaca_repo(butaca_id, cambios)
    except pymysql.err.IntegrityError as causa:
        raise ValueError(construir_error_api(
            "butaca.duplicada",
            "Butaca duplicada",
            "La fila y el número ya existen en la sala.",
        ), 409) from causa


def eliminar_butaca(butaca_id):
    _exigir_butaca(butaca_id)
    try:
        eliminar_butaca_repo(butaca_id)
    except pymysql.err.IntegrityError as causa:
        raise ValueError(construir_error_api(
            "butaca.has.reservas",
            "No se puede eliminar",
            "La butaca tiene entradas relacionadas.",
        ), 409) from causa


def eliminar_butacas_sala(sala_id):
    _exigir_sala(sala_id)
    try:
        eliminar_butacas_de_sala_repo(sala_id)
    except pymysql.err.IntegrityError as causa:
        raise ValueError(construir_error_api(
            "butacas.has.reservas",
            "No se pueden eliminar",
            "Las butacas tienen entradas relacionadas.",
        ), 409) from causa
