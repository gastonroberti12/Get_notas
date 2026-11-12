import pymysql

from cine_fuente.repositories import resenas as resenas_repo
from cine_fuente.repositories.peliculas import consultar_pelicula_por_id
from cine_fuente.utils import construir_error_api, formatear_fecha_hora


def error(codigo, titulo, mensaje, status):
    raise ValueError(construir_error_api(codigo, titulo, mensaje), status)


def verificar_pelicula(pelicula_id):
    if consultar_pelicula_por_id(pelicula_id) is None:
        error("PELICULA_NO_ENCONTRADA", "Película no encontrada",
              f"No existe la película {pelicula_id}.", 404)


def resena_api(fila):
    """Adapta una reseña al JSON. Del autor solo se muestra el nombre y la inicial del apellido."""
    inicial = fila["apellido"][:1].upper() + "." if fila["apellido"] else ""
    return {
        "id": int(fila["id"]),
        "calificacion": int(fila["calificacion"]),
        "comentario": fila["comentario"],
        "fecha": formatear_fecha_hora(fila["fecha"]),
        "autor": f"{fila['nombre']} {inicial}".strip(),
    }


def listar_resenas(pelicula_id, limit, offset):
    verificar_pelicula(pelicula_id)
    filas = resenas_repo.listar_resenas(pelicula_id, limit, offset)
    resumen = resenas_repo.resumen_resenas(pelicula_id)
    promedio = resumen["promedio"]
    return {
        "resenas": [resena_api(fila) for fila in filas],
        "total": int(resumen["total"]),
        "promedio": round(float(promedio), 1) if promedio is not None else None,
    }


def estado_usuario(usuario_id, pelicula_id):
    """Dice si el usuario ya reseñó la película y si puede hacerlo."""
    verificar_pelicula(pelicula_id)
    ya_reseno = resenas_repo.obtener_resena_usuario(usuario_id, pelicula_id) is not None
    vio_pelicula = resenas_repo.usuario_vio_pelicula(usuario_id, pelicula_id)
    return {
        "vio_pelicula": vio_pelicula,
        "ya_reseno": ya_reseno,
        "puede_resenar": vio_pelicula and not ya_reseno,
    }


def crear_resena(usuario_id, pelicula_id, calificacion, comentario):
    verificar_pelicula(pelicula_id)

    if not resenas_repo.usuario_vio_pelicula(usuario_id, pelicula_id):
        error("RESENA_NO_PERMITIDA", "No podés reseñar esta película",
              "Solo podés reseñar películas cuya entrada ya fue validada en el cine.", 403)

    if resenas_repo.obtener_resena_usuario(usuario_id, pelicula_id) is not None:
        error("RESENA_DUPLICADA", "Ya reseñaste esta película",
              "Solo se permite una reseña por película.", 409)

    try:
        resena_id = resenas_repo.insertar_resena(usuario_id, pelicula_id, calificacion, comentario)
    except pymysql.err.IntegrityError:
        # dos pedidos casi simultáneos: la restricción UNIQUE de la tabla frena el segundo
        error("RESENA_DUPLICADA", "Ya reseñaste esta película",
              "Solo se permite una reseña por película.", 409)

    return {
        "id": int(resena_id),
        "pelicula_id": pelicula_id,
        "calificacion": calificacion,
        "comentario": comentario,
    }