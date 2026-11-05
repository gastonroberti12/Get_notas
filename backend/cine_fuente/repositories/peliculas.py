from cine_fuente.db import ejecutar_consulta, ejecutar_escritura


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
    if activa is None:
        return ejecutar_consulta("SELECT * FROM pelicula ORDER BY id")
    return ejecutar_consulta("SELECT * FROM pelicula WHERE activa = %s ORDER BY id", (activa,))


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


# Consulta las películas activas con funciones futuras en una sucursal.
def consultar_peliculas_por_sucursal(sucursal_id, desde):
    return ejecutar_consulta(
        "SELECT p.* FROM pelicula p "
        "JOIN funcion f ON f.pelicula_id = p.id "
        "JOIN salas s ON s.id = f.sala_id "
        "WHERE p.activa = TRUE AND s.sucursal_id = %s AND f.fecha_hora > %s "
        "GROUP BY p.id ORDER BY p.id",
        (sucursal_id, desde),
    )