import pymysql

from cine_fuente.repositories.funciones_repository import (
    actualizar_funcion, consultar_funcion_por_id, consultar_funciones,
    desactivar_funcion, eliminar_funcion, insertar_funcion,
)
from cine_fuente.repositories.peliculas import consultar_pelicula_por_id
from cine_fuente.repositories.salas import consultar_sala_por_id
from cine_fuente.utils import construir_error_api


# Obtiene el listado de funciones según los filtros.
def obtener_funciones(filtros, limit, offset):
    funciones = consultar_funciones(filtros["pelicula_id"], filtros["sala_id"], filtros["activa"])
    return funciones[offset:offset + limit], len(funciones)


# Busca una función por su identificador.
def obtener_funcion_por_id(funcion_id):
    funcion = consultar_funcion_por_id(funcion_id)
    if funcion is None:
        raise ValueError(construir_error_api("funcion.not.found", "Función no encontrada", "La función solicitada no existe."))
    return funcion


# Registra una nueva función.
def crear_funcion(pelicula_id, sala_id, fecha_hora, precio):
    validar_relaciones(pelicula_id, sala_id)
    try:
        funcion_id = insertar_funcion(pelicula_id, sala_id, fecha_hora, precio)
    except pymysql.err.IntegrityError as causa:
        raise ValueError(construir_error_api("funcion.overlap", "Horario ocupado", "Ya existe una función en esa sala y horario.")) from causa
    return obtener_funcion_por_id(funcion_id)


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
