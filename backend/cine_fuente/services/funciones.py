import pymysql
from datetime import timedelta, timezone

from cine_fuente.db import ejecutar_transaccion
from cine_fuente.repositories.funciones_repository import (
    consultar_funcion_por_id, consultar_funciones,
    desactivar_funcion, eliminar_funcion, bloquear_sala_para_funcion,
    consultar_funciones_sala_en_transaccion, insertar_funcion_en_transaccion,
    obtener_pelicula_para_funcion, obtener_funcion_para_actualizar,
    contar_reservas_de_funcion,
    actualizar_funcion_en_transaccion as guardar_cambios_funcion_en_transaccion,
)
from cine_fuente.utils import ahora_gmt3, construir_error_api, formatear_fecha_hora


# Obtiene el listado de funciones según los filtros.
def obtener_funciones(filtros, limit, offset):
    funciones = consultar_funciones(
        pelicula_id=filtros["pelicula_id"],
        sala_id=filtros["sala_id"],
        sucursal_id=filtros["sucursal_id"],
        activa=filtros["activa"],
        fecha=filtros["fecha"],
    )
    pagina = funciones[offset:offset + limit]
    for f in pagina:
        f["fecha_hora"] = formatear_fecha_hora(f["fecha_hora"])
    return pagina, len(funciones)


# Busca una función por su identificador.
def obtener_funcion_por_id(funcion_id):
    funcion = consultar_funcion_por_id(funcion_id)
    if funcion is None:
        raise ValueError(construir_error_api("funcion.not.found", "Función no encontrada", "La función solicitada no existe."))
    funcion["fecha_hora"] = formatear_fecha_hora(funcion["fecha_hora"])
    return funcion


# Registra una nueva función.
def crear_funcion(pelicula_id, sala_id, fecha_hora, precio):
    try:
        funcion_id = ejecutar_transaccion(
            lambda cursor: _crear_funcion_en_transaccion(
                cursor, pelicula_id, sala_id, fecha_hora, precio
            )
        )
    except pymysql.err.IntegrityError as causa:
        raise ValueError(construir_error_api("funcion.overlap", "Horario ocupado", "Ya existe una función en esa sala y horario.")) from causa
    return obtener_funcion_por_id(funcion_id)


def _crear_funcion_en_transaccion(cursor, pelicula_id, sala_id, fecha_hora, precio):
    inicio = validar_programacion_funcion_pelicula(
        cursor, pelicula_id, sala_id, fecha_hora
    )
    return insertar_funcion_en_transaccion(
        cursor, pelicula_id, sala_id, inicio, precio
    )


def validar_programacion_funcion_pelicula(
    cursor, pelicula_id, sala_id, fecha_hora, excluir_funcion_id=None
):
    pelicula = obtener_pelicula_para_funcion(cursor, pelicula_id)
    if pelicula is None:
        raise ValueError(construir_error_api(
            "pelicula.not.found", "Película no encontrada",
            "La película indicada no existe.",
        ), 404)

    sala = bloquear_sala_para_funcion(cursor, sala_id)
    if sala is None:
        raise ValueError(construir_error_api(
            "sala.not.found", "Sala no encontrada",
            "La sala indicada no existe.",
        ), 404)

    if not pelicula["activa"]:
        raise ValueError(construir_error_api(
            "pelicula.inactive", "Película inactiva",
            "No se puede crear una función para una película inactiva.",
        ), 409)

    inicio = _fecha_local_sin_zona(fecha_hora)
    duracion = pelicula["duracion_min"]
    if duracion is None or duracion <= 0:
        raise ValueError(construir_error_api(
            "pelicula.duration.invalid", "Duración inválida",
            "La película debe tener una duración válida.",
        ), 400)

    fin_proyeccion = inicio + timedelta(minutes=duracion)
    cartelera_inicio = _fecha_local_sin_zona(pelicula["fecha_inicio_cartelera"])
    cartelera_fin = _fecha_local_sin_zona(pelicula["fecha_fin_cartelera"])
    if (
        cartelera_inicio is None
        or cartelera_fin is None
        or inicio < cartelera_inicio
        or fin_proyeccion > cartelera_fin
    ):
        raise ValueError(construir_error_api(
            "funcion.outside.movie_schedule", "Función fuera de cartelera",
            "La función debe estar dentro del período de cartelera de la película.",
        ), 409)

    fin_intervalo = fin_proyeccion + timedelta(minutes=30)
    for funcion in consultar_funciones_sala_en_transaccion(
        cursor, sala_id, excluir_funcion_id
    ):
        existente_inicio = _fecha_local_sin_zona(funcion["fecha_hora"])
        existente_duracion = funcion["duracion_min"]
        if existente_inicio is None or existente_duracion is None:
            continue
        existente_fin = existente_inicio + timedelta(
            minutes=existente_duracion + 30
        )
        if inicio < existente_fin and existente_inicio < fin_intervalo:
            raise ValueError(construir_error_api(
                "funcion.overlap", "Horario ocupado",
                "La sala no tiene el margen necesario entre funciones.",
            ), 409)

    return inicio


def _fecha_local_sin_zona(valor):
    if valor is None:
        return None
    if valor.tzinfo is not None:
        return valor.astimezone(timezone(timedelta(hours=-3))).replace(tzinfo=None)
    return valor


# Actualiza los datos de una función existente.
def actualizar_funcion_por_id(funcion_id, cambios):
    try:
        ejecutar_transaccion(
            lambda cursor: actualizar_funcion_en_transaccion(
                cursor, funcion_id, cambios
            )
        )
    except pymysql.err.IntegrityError as causa:
        raise ValueError(construir_error_api("funcion.overlap", "Horario ocupado", "Ya existe una función en esa sala y horario.")) from causa


def actualizar_funcion_en_transaccion(cursor, funcion_id, cambios):
    funcion = obtener_funcion_para_actualizar(cursor, funcion_id)
    if funcion is None:
        raise ValueError(construir_error_api(
            "funcion.not.found", "Función no encontrada",
            "La función solicitada no existe.",
        ))

    campos_protegidos = {"pelicula_id", "sala_id", "fecha_hora"}
    if campos_protegidos.intersection(cambios) and contar_reservas_de_funcion(
        cursor, funcion_id
    ):
        raise ValueError(construir_error_api(
            "funcion.has.reservas", "No se puede modificar la función",
            "La función tiene reservas asociadas y no se puede cambiar su película, sala u horario.",
        ), 409)

    pelicula_id = cambios.get("pelicula_id", funcion["pelicula_id"])
    sala_id = cambios.get("sala_id", funcion["sala_id"])
    fecha_hora = cambios.get("fecha_hora", funcion["fecha_hora"])
    reactivando = cambios.get("activa") is True and not funcion["activa"]
    # Una función que ya pasó no se puede volver a dar de alta.
    if reactivando and _fecha_local_sin_zona(fecha_hora) < ahora_gmt3().replace(tzinfo=None):
        raise ValueError(construir_error_api(
            "funcion.past", "Función ya realizada",
            "No se puede dar de alta una función que ya pasó.",
        ), 409)
    requiere_validar_programacion = (
        bool(campos_protegidos.intersection(cambios)) or reactivando
    )
    if requiere_validar_programacion:
        inicio = validar_programacion_funcion_pelicula(
            cursor,
            pelicula_id,
            sala_id,
            fecha_hora,
            excluir_funcion_id=funcion_id,
        )
        if "fecha_hora" in cambios:
            cambios["fecha_hora"] = inicio

    guardar_cambios_funcion_en_transaccion(cursor, funcion_id, cambios)


# Elimina o desactiva una función.
def eliminar_funcion_por_id(funcion_id, fisica=False):
    obtener_funcion_por_id(funcion_id)
    if fisica:
        try:
            eliminar_funcion(funcion_id)
        except pymysql.err.IntegrityError as causa:
            raise ValueError(construir_error_api("funcion.has.reservas", "No se puede eliminar", "La función tiene datos relacionados.")) from causa
    else:
        desactivar_funcion(funcion_id)
