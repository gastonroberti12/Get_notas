from cine_fuente.db import ejecutar_consulta, ejecutar_escritura


# Consulta las funciones registradas.
def consultar_funciones(pelicula_id=None, sala_id=None, activa=None):
    sql = (
        "SELECT f.id, f.pelicula_id, p.titulo AS pelicula, f.sala_id, s.nombre AS sala, "
        "f.fecha_hora, f.precio, f.activa "
        "FROM funcion f JOIN pelicula p ON p.id = f.pelicula_id "
        "JOIN salas s ON s.id = f.sala_id WHERE 1 = 1"
    )
    params = []
    if pelicula_id is not None:
        sql += " AND f.pelicula_id = %s"
        params.append(pelicula_id)
    if sala_id is not None:
        sql += " AND f.sala_id = %s"
        params.append(sala_id)
    if activa is not None:
        sql += " AND f.activa = %s"
        params.append(activa)
    sql += " ORDER BY f.fecha_hora"
    return ejecutar_consulta(sql, tuple(params))


# Busca una función por su identificador.
def consultar_funcion_por_id(funcion_id):
    filas = ejecutar_consulta(
        "SELECT f.id, f.pelicula_id, p.titulo AS pelicula, f.sala_id, s.nombre AS sala, "
        "f.fecha_hora, f.precio, f.activa "
        "FROM funcion f JOIN pelicula p ON p.id = f.pelicula_id "
        "JOIN salas s ON s.id = f.sala_id WHERE f.id = %s",
        (funcion_id,),
    )
    return filas[0] if filas else None


# Guarda una nueva función.
def insertar_funcion(pelicula_id, sala_id, fecha_hora, precio):
    return ejecutar_escritura(
        "INSERT INTO funcion (pelicula_id, sala_id, fecha_hora, precio, activa) "
        "VALUES (%s, %s, %s, %s, TRUE)",
        (pelicula_id, sala_id, fecha_hora, precio),
    )


# Modifica los datos de una función.
def actualizar_funcion(funcion_id, datos):
    campos = ", ".join(f"{campo} = %s" for campo in datos)
    ejecutar_escritura(f"UPDATE funcion SET {campos} WHERE id = %s", (*datos.values(), funcion_id))


# Marca una función como inactiva.
def desactivar_funcion(funcion_id):
    ejecutar_escritura("UPDATE funcion SET activa = FALSE WHERE id = %s", (funcion_id,),)


# Elimina una función físicamente.
def eliminar_funcion(funcion_id):
    ejecutar_escritura("DELETE FROM funcion WHERE id = %s", (funcion_id,),)
