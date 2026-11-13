from cine_fuente.db import ejecutar_consulta, ejecutar_escritura
from cine_fuente.utils import ahora_gmt3


def listar_resenas(pelicula_id, limit, offset):
    """Reseñas de una película, de la más nueva a la más vieja."""
    sql = """
        SELECT r.id, r.calificacion, r.comentario, r.fecha, u.nombre, u.apellido
        FROM resenas AS r
        INNER JOIN usuarios AS u ON u.id = r.usuario_id
        WHERE r.pelicula_id = %(pelicula_id)s
        ORDER BY r.fecha DESC, r.id DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """
    return ejecutar_consulta(
        sql, {"pelicula_id": pelicula_id, "limit": limit, "offset": offset}
    )


def resumen_resenas(pelicula_id):
    """Cantidad de reseñas y calificación promedio de una película."""
    sql = """
        SELECT COUNT(*) AS total, AVG(calificacion) AS promedio
        FROM resenas
        WHERE pelicula_id = %(pelicula_id)s
    """
    return ejecutar_consulta(sql, {"pelicula_id": pelicula_id})[0]


def obtener_resena_usuario(usuario_id, pelicula_id):
    """Devuelve la reseña que el usuario ya hizo de la película, o None."""
    sql = """
        SELECT id, calificacion, comentario
        FROM resenas
        WHERE usuario_id = %(usuario_id)s AND pelicula_id = %(pelicula_id)s
    """
    filas = ejecutar_consulta(sql, {"usuario_id": usuario_id, "pelicula_id": pelicula_id})
    return filas[0] if filas else None


def usuario_vio_pelicula(usuario_id, pelicula_id):
    """True si el usuario tiene al menos una entrada ya validada (fecha_uso) de la película."""
    sql = """
        SELECT 1 AS visto
        FROM entrada AS e
        INNER JOIN reservas AS r ON r.id = e.reserva_id
        INNER JOIN funcion AS f ON f.id = r.funcion_id
        WHERE r.usuario_id = %(usuario_id)s
          AND f.pelicula_id = %(pelicula_id)s
          AND e.fecha_uso IS NOT NULL
        LIMIT 1
    """
    filas = ejecutar_consulta(sql, {"usuario_id": usuario_id, "pelicula_id": pelicula_id})
    return len(filas) > 0


def insertar_resena(usuario_id, pelicula_id, calificacion, comentario):
    sql = """
        INSERT INTO resenas (usuario_id, pelicula_id, calificacion, comentario, fecha)
        VALUES (%(usuario_id)s, %(pelicula_id)s, %(calificacion)s, %(comentario)s, %(fecha)s)
    """
    return ejecutar_escritura(sql, {
        "usuario_id": usuario_id,
        "pelicula_id": pelicula_id,
        "calificacion": calificacion,
        "comentario": comentario,
        "fecha": ahora_gmt3().replace(tzinfo=None),  # la base de TiDB está en UTC
    })


def listar_resenas_usuario(usuario_id, limit, offset):
    """Reseñas que escribió un usuario, con los datos de la película."""
    sql = """
        SELECT r.id, r.pelicula_id, r.calificacion, r.comentario, r.fecha,
               p.titulo AS pelicula, p.poster_url
        FROM resenas AS r
        INNER JOIN pelicula AS p ON p.id = r.pelicula_id
        WHERE r.usuario_id = %(usuario_id)s
        ORDER BY r.fecha DESC, r.id DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """
    return ejecutar_consulta(
        sql, {"usuario_id": usuario_id, "limit": limit, "offset": offset}
    )


def contar_resenas_usuario(usuario_id):
    sql = "SELECT COUNT(*) AS total FROM resenas WHERE usuario_id = %(usuario_id)s"
    return ejecutar_consulta(sql, {"usuario_id": usuario_id})[0]["total"]


