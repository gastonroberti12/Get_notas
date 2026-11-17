import pymysql
from datetime import timedelta, timezone

from cine_fuente.db import ejecutar_transaccion
from cine_fuente.repositories.funciones_repository import (
    actualizar_funcion, consultar_funcion_por_id, consultar_funciones,
    desactivar_funcion, eliminar_funcion, bloquear_sala_para_funcion,
    consultar_funciones_sala_en_transaccion, insertar_funcion_en_transaccion,
    obtener_pelicula_para_funcion,
)
from cine_fuente.repositories.peliculas import consultar_pelicula_por_id
from cine_fuente.repositories.salas import consultar_sala_por_id
from cine_fuente.utils import construir_error_api, formatear_fecha_hora


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
    for funcion in consultar_funciones_sala_en_transaccion(cursor, sala_id):
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

    return insertar_funcion_en_transaccion(
        cursor, pelicula_id, sala_id, inicio, precio
    )


def _fecha_local_sin_zona(valor):
    if valor is None:
        return None
    if valor.tzinfo is not None:
        return valor.astimezone(timezone(timedelta(hours=-3))).replace(tzinfo=None)
    return valor


# Verifica las relaciones necesarias para una función.
def validar_relaciones(pelicula_id, sala_id):
    if consultar_pelicula_por_id(pelicula_id) is None:
        raise ValueError(construir_error_api("pelicula.not.found", "Película no encontrada", "La película indicada no existe."))
    if consultar_sala_por_id(sala_id) is None:
        raise ValueError(construir_error_api("sala.not.found", "Sala no encontrada", "La sala indicada no existe."))


# Actualiza los datos de una función existente.
def actualizar_funcion_por_id(funcion_id, cambios):
    obtener_funcion_por_id(funcion_id)
    if "pelicula_id" in cambios:
        validar_relaciones(cambios["pelicula_id"], consultar_funcion_por_id(funcion_id)["sala_id"])
    if "sala_id" in cambios:
        validar_relaciones(consultar_funcion_por_id(funcion_id)["pelicula_id"], cambios["sala_id"])
    try:
        actualizar_funcion(funcion_id, cambios)
    except pymysql.err.IntegrityError as causa:
        raise ValueError(construir_error_api("funcion.overlap", "Horario ocupado", "Ya existe una función en esa sala y horario.")) from causa


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
