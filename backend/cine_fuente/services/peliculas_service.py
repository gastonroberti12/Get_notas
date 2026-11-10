import pymysql

from cine_fuente.repositories.peliculas import (
    actualizar_pelicula,
    consultar_peliculas,
    consultar_peliculas_por_sucursal,
    insertar_pelicula,
    tiene_reservas_activas,
)
from cine_fuente.utils import ahora_gmt3, construir_error_api, formatear_fecha_hora


# Lista las películas; con sucursal, solo las que tienen funciones futuras ahí.
def obtener_peliculas(filtros):
    if filtros["sucursal_id"] is None:
        return consultar_peliculas(filtros["activa"])
    return consultar_peliculas_por_sucursal(
        filtros["sucursal_id"], ahora_gmt3().replace(tzinfo=None)
    )


def insertar_pelicula_segura(datos):
    try:
        return insertar_pelicula(datos)
    except pymysql.err.IntegrityError as error:
        if error.args and error.args[0] == 1062:
            raise ValueError(construir_error_api(
                "pelicula.already.exists",
                "Película duplicada",
                "La película ya existe en la cartelera.",
            ), 409) from error
        raise


def formatear_pelicula(fila):
    pelicula = dict(fila)
    pelicula["fecha_inicio_cartelera"] = formatear_fecha_hora(
        pelicula["fecha_inicio_cartelera"]
    )
    pelicula["fecha_fin_cartelera"] = formatear_fecha_hora(
        pelicula["fecha_fin_cartelera"]
    )
    pelicula["activa"] = bool(pelicula["activa"])
    return pelicula


def dar_de_baja(pelicula_id):
    if tiene_reservas_activas(pelicula_id):
        return False
    actualizar_pelicula(pelicula_id, {"activa": False})
    return True