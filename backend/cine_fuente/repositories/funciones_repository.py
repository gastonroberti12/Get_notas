from datetime import timedelta

from cine_fuente.db import ejecutar_consulta, ejecutar_escritura
from cine_fuente.utils import ahora_gmt3

#constante para simplificar consultar_funciones y consultar_funcion_por_id
SELECT_FUNCION = (
    "SELECT f.id, f.pelicula_id, p.titulo AS pelicula, f.sala_id, s.nombre AS sala, "
    "su.nombre AS sucursal, f.fecha_hora, f.precio, f.activa "
    "FROM funcion f JOIN pelicula p ON p.id = f.pelicula_id "
    "JOIN salas s ON s.id = f.sala_id JOIN sucursales su ON su.id = s.sucursal_id"
)


# Consulta las funciones registradas.
def consultar_funciones(
    pelicula_id=None,
    sala_id=None,
    activa=None,
    sucursal_id=None,
    fecha=None,
):
    sql = SELECT_FUNCION + " WHERE 1 = 1"
    params = []
    if pelicula_id is not None:
        sql += " AND f.pelicula_id = %s"
        params.append(pelicula_id)
    if sala_id is not None:
        sql += " AND f.sala_id = %s"
        params.append(sala_id)
    if sucursal_id is not None:
        sql += " AND s.sucursal_id = %s"
        params.append(sucursal_id)
    if fecha is not None:
        sql += " AND f.fecha_hora >= %s AND f.fecha_hora < %s"
        params.extend([fecha, fecha + timedelta(days=1)])
    if activa is not None:
        # Activas = vigentes y futuras; inactivas = dadas de baja o ya pasadas.
        sql += " AND f.activa = TRUE AND f.fecha_hora >= %s" if activa else " AND (f.activa = FALSE OR f.fecha_hora < %s)"
        params.append(ahora_gmt3().replace(tzinfo=None))
    sql += " ORDER BY f.fecha_hora"
    return ejecutar_consulta(sql, tuple(params))


# Busca una función por su identificador.
def consultar_funcion_por_id(funcion_id):
    filas = ejecutar_consulta(SELECT_FUNCION + " WHERE f.id = %s", (funcion_id,))
    return filas[0] if filas else None


# Guarda una nueva función.
def insertar_funcion(pelicula_id, sala_id, fecha_hora, precio):
    return ejecutar_escritura(
        "INSERT INTO funcion (pelicula_id, sala_id, fecha_hora, precio, activa) "
        "VALUES (%s, %s, %s, %s, TRUE)",
        (pelicula_id, sala_id, fecha_hora, precio),
    )


def obtener_pelicula_para_funcion(cursor, pelicula_id):
    cursor.execute(
        "SELECT id, activa, fecha_inicio_cartelera, fecha_fin_cartelera, duracion_min "
        "FROM pelicula WHERE id = %s",
        (pelicula_id,),
    )
    return cursor.fetchone()


def bloquear_sala_para_funcion(cursor, sala_id):
    cursor.execute("SELECT id FROM salas WHERE id = %s FOR UPDATE", (sala_id,))
    return cursor.fetchone()


def consultar_funciones_sala_en_transaccion(
    cursor, sala_id, excluir_funcion_id=None
):
    sql = (
        "SELECT f.id, f.fecha_hora, p.duracion_min "
        "FROM funcion f JOIN pelicula p ON p.id = f.pelicula_id "
        "WHERE f.sala_id = %s"
    )
    parametros = [sala_id]
    if excluir_funcion_id is not None:
        sql += " AND f.id <> %s"
        parametros.append(excluir_funcion_id)
    cursor.execute(sql, tuple(parametros))
    return cursor.fetchall()


def insertar_funcion_en_transaccion(cursor, pelicula_id, sala_id, fecha_hora, precio):
    cursor.execute(
        "INSERT INTO funcion (pelicula_id, sala_id, fecha_hora, precio, activa) "
        "VALUES (%s, %s, %s, %s, TRUE)",
        (pelicula_id, sala_id, fecha_hora, precio),
    )
    return cursor.lastrowid


def obtener_funcion_para_actualizar(cursor, funcion_id):
    cursor.execute(
        "SELECT id, pelicula_id, sala_id, fecha_hora, activa "
        "FROM funcion WHERE id = %s FOR UPDATE",
        (funcion_id,),
    )
    return cursor.fetchone()


def contar_reservas_de_funcion(cursor, funcion_id):
    cursor.execute(
        "SELECT COUNT(*) AS cantidad FROM reservas WHERE funcion_id = %s",
        (funcion_id,),
    )
    return cursor.fetchone()["cantidad"]


def existe_pelicula(cursor, pelicula_id):
    cursor.execute("SELECT id FROM pelicula WHERE id = %s", (pelicula_id,))
    return cursor.fetchone() is not None


def existe_sala(cursor, sala_id):
    cursor.execute("SELECT id FROM salas WHERE id = %s", (sala_id,))
    return cursor.fetchone() is not None


def actualizar_funcion_en_transaccion(cursor, funcion_id, datos):
    campos = ", ".join(f"{campo} = %s" for campo in datos)
    cursor.execute(
        f"UPDATE funcion SET {campos} WHERE id = %s",
        (*datos.values(), funcion_id),
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
