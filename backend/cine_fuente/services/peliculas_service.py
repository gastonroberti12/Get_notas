from cine_fuente.repositories.peliculas import (
    actualizar_pelicula,
    consultar_peliculas,
    consultar_peliculas_por_sucursal,
    tiene_reservas_activas,
)
from cine_fuente.services.reservas import procesar_expiraciones
from cine_fuente.utils import ahora_gmt3, formatear_fecha_hora


# Lista las películas; con sucursal, solo las que tienen funciones futuras ahí.
def obtener_peliculas(filtros):
    if filtros["sucursal_id"] is None:
        return consultar_peliculas(filtros["activa"])
    return consultar_peliculas_por_sucursal(
        filtros["sucursal_id"], ahora_gmt3().replace(tzinfo=None)
    )


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
    procesar_expiraciones()
    if tiene_reservas_activas(pelicula_id):
        return False
    actualizar_pelicula(pelicula_id, {"activa": False})
    return True