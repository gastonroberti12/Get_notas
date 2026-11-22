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
def consultar_peliculas(activa=None, sucursal_id=None, titulo=None, genero=None):
    ahora = ahora_gmt3().replace(tzinfo=None)
    condiciones = []
    parametros = []

    if sucursal_id is not None:
        condiciones.extend([
            "activa = TRUE",
            "fecha_fin_cartelera >= %s",
            "id IN ("
            "SELECT f.pelicula_id FROM funcion f "
            "JOIN salas s ON s.id = f.sala_id "
            "WHERE f.activa = TRUE AND s.sucursal_id = %s AND f.fecha_hora > %s"
            ")",
        ])
        parametros.extend([ahora, sucursal_id, ahora])
        if activa is not None:
            condiciones.append("activa = %s")
            parametros.append(activa)
    elif activa is None:
        condiciones.extend(["activa = TRUE", "fecha_fin_cartelera >= %s"])
        parametros.append(ahora)
    else:
        condiciones.append("activa = %s")
        parametros.append(activa)

    if titulo is not None:
        condiciones.append("LOWER(titulo) LIKE LOWER(%s)")
        parametros.append(f"%{titulo}%")
    if genero is not None:
        condiciones.append("LOWER(genero) LIKE LOWER(%s)")
        parametros.append(f"%{genero}%")

    return ejecutar_consulta(
        f"SELECT * FROM pelicula WHERE {' AND '.join(condiciones)} ORDER BY id",
        tuple(parametros),
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


def consultar_peliculas_por_sucursal(sucursal_id, desde=None):
    """Compatibilidad para consultas por sucursal; `desde` se conserva por API interna."""
    return consultar_peliculas(sucursal_id=sucursal_id)
