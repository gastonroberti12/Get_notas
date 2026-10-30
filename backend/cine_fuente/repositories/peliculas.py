from cine_fuente.db import ejecutar_consulta, ejecutar_escritura


# Busca una película por su identificador.
def consultar_pelicula_por_id(pelicula_id):
    filas = ejecutar_consulta("SELECT * FROM pelicula WHERE id = %s", (pelicula_id,),)
    return filas[0] if filas else None


# Busca una película por su ID de IMDb.
def consultar_pelicula_por_imdb(imdb_id):
    filas = ejecutar_consulta("SELECT * FROM pelicula WHERE id_externo = %s", (imdb_id,),)
    return filas[0] if filas else None


# Consulta las películas almacenadas.
def consultar_peliculas():
    return ejecutar_consulta("SELECT * FROM pelicula ORDER BY id")


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
