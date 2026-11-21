from urllib.parse import urlencode
from services.api_cliente import LIMITE_LISTADOS, llamar_api

# pedidos al backend sobre películas, sus reseñas y la busqueda en OMDb.


def listar_peliculas(filtros=""):
    return llamar_api("GET", f"/peliculas?_limit={LIMITE_LISTADOS}{filtros}")


def obtener_pelicula(pelicula_id):
    return llamar_api("GET", f"/peliculas/{pelicula_id}")


def crear_pelicula(datos):
    return llamar_api("POST", "/peliculas", datos)


def actualizar_pelicula(pelicula_id, cambios):
    return llamar_api("PATCH", f"/peliculas/{pelicula_id}", cambios)


def actualizar_estado_pelicula(pelicula_id, activa):
    return llamar_api("PATCH", f"/peliculas/{pelicula_id}", {"activa": activa})


def buscar_en_omdb(texto, pagina):
    return llamar_api("GET", "/peliculas/buscar?" + urlencode({"q": texto, "pagina": pagina}))


def obtener_datos_omdb(imdb_id):
    return llamar_api("GET", f"/peliculas/{imdb_id}")


def obtener_resenas(pelicula_id):
    # ademas de la lista, el backend devuelve el total y el promedio de las reseñas.
    return llamar_api("GET", f"/peliculas/{pelicula_id}/resenas?_limit=50")


def obtener_estado_resena(pelicula_id):
    return llamar_api("GET", f"/peliculas/{pelicula_id}/resenas/estado")


def publicar_resena(pelicula_id, calificacion, comentario):
    datos = {"calificacion": calificacion, "comentario": comentario or None}
    return llamar_api("POST", f"/peliculas/{pelicula_id}/resenas", datos)