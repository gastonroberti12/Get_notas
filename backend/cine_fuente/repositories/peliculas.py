from cine_fuente.db import ejecutar_consulta, ejecutar_escritura
from cine_fuente.utils import ahora_gmt3


# Busca una película por su identificador.
def consultar_pelicula_por_id(pelicula_id):
    filas = ejecutar_consulta("SELECT * FROM pelicula WHERE id = %s", (pelicula_id,),)
    return filas[0] if filas else None


# Busca una película por su ID de IMDb.
def consultar_pelicula_por_imdb(imdb_id):
    filas = ejecutar_consulta("SELECT * FROM pelicula WHERE id_externo = %s", (imdb_id,),)
    return filas[0] if filas else None


# Consulta las películas almacenadas; con activa, filtra por ese estado.
def consultar_peliculas(activa=None):
    if activa is False:
        return ejecutar_consulta(
            "SELECT * FROM pelicula WHERE activa = FALSE ORDER BY id"
        )
    ahora = ahora_gmt3().replace(tzinfo=None)
    return ejecutar_consulta(
        "SELECT * FROM pelicula "
        "WHERE activa = TRUE "
        "AND fecha_fin_cartelera >= %s "
        "ORDER BY id",
        (ahora,),
    )


# Guarda los datos básicos de una película.
def insertar_pelicula(datos):
    columnas = (
        "titulo", "sinopsis", "poster_url", "duracion_min", "clasificacion", "genero",
        "id_externo", "fecha_inicio_cartelera", "fecha_fin_cartelera", "activa",
    )
    presentes = [columna for columna in columnas if columna in datos]
    marcadores = ", ".join(["%s"] * len(presentes))
    return ejecutar_escritura(
        f"INSERT INTO pelicula ({', '.join(presentes)}) VALUES ({marcadores})",
        tuple(datos[columna] for columna in presentes),
    )


# Actualiza una película existente.
def actualizar_pelicula(pelicula_id, datos):
    campos = ", ".join(f"{campo} = %s" for campo in datos)
    ejecutar_escritura(f"UPDATE pelicula SET {campos} WHERE id = %s", (*datos.values(), pelicula_id))


def tiene_reservas_activas(pelicula_id):
    filas = ejecutar_consulta(
        "SELECT COUNT(*) AS cantidad "
        "FROM reservas r "
        "JOIN funcion f ON f.id = r.funcion_id "
        "JOIN pelicula p ON p.id = f.pelicula_id "
        "WHERE p.id = %s "
        "AND r.estado IN ('pendiente', 'confirmada') "
        "AND f.fecha_hora > %s",
        (pelicula_id, ahora_gmt3().replace(tzinfo=None)),
    )
    return filas[0]["cantidad"] > 0


# Consulta las películas activas con funciones futuras en una sucursal.
def consultar_peliculas_por_sucursal(sucursal_id, desde):
    return ejecutar_consulta(
        "SELECT * FROM pelicula "
        "WHERE activa = TRUE AND id IN ("
        "  SELECT f.pelicula_id FROM funcion f "
        "  JOIN salas s ON s.id = f.sala_id "
        "  WHERE f.activa = TRUE AND s.sucursal_id = %s AND f.fecha_hora > %s"
        ") ORDER BY id",
        (sucursal_id, desde),
    )