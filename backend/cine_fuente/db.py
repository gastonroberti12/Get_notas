import os
import certifi # Para obtener los certificados de confianza
import pymysql

from pymysql.cursors import DictCursor

from constants import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def obtener_conexion():

    configuracion_ssl = {}

    if os.getenv("DB_SSL", "false").lower() == "true": # Habilita TLS
        configuracion_ssl = {
            "ssl_ca": certifi.where(),
            "ssl_verify_cert": True,
            "ssl_verify_identity": True
        }

    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=DictCursor,
        read_timeout=60,
        write_timeout=60,
        connect_timeout=15, # Por TiDB tarda en responder, la petición no queda colgada y corta a los 15 s
        **configuracion_ssl
    )


def ejecutar_consulta(sql, params=None):
    with obtener_conexion() as conexion, conexion.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def ejecutar_escritura(sql, params=None):
    with obtener_conexion() as conexion, conexion.cursor() as cursor:
        cursor.execute(sql, params)
        conexion.commit()
        return cursor.lastrowid


def ejecutar_actualizacion(sql, params=None):
    with obtener_conexion() as conexion, conexion.cursor() as cursor:
        cursor.execute(sql, params)
        conexion.commit()
        return cursor.rowcount