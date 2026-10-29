import pymysql
from pymysql.cursors import DictCursor

from constants import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER



def obtener_conexion():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4", #para tildes 
        cursorclass=DictCursor,
    )


def ejecutar_consulta(sql, params=None):
    """Ejecuta un SELECT y devuelve una lista de diccionarios."""
    with obtener_conexion() as conexion, conexion.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def ejecutar_escritura(sql, params=None):
    """Ejecuta un INSERT/UPDATE/DELETE, confirma y devuelve el id generado."""
    with obtener_conexion() as conexion, conexion.cursor() as cursor:
        cursor.execute(sql, params)
        conexion.commit()
        return cursor.lastrowid