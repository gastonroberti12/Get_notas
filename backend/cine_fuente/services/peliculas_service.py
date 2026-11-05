from cine_fuente.repositories.peliculas import (
    consultar_peliculas,
    consultar_peliculas_por_sucursal,
)
from cine_fuente.utils import ahora_gmt3


# Lista las películas; con sucursal, solo las que tienen funciones futuras ahí.
def obtener_peliculas(filtros):
    if filtros["sucursal_id"] is None:
        return consultar_peliculas(filtros["activa"])
    return consultar_peliculas_por_sucursal(
        filtros["sucursal_id"], ahora_gmt3().replace(tzinfo=None)
    )