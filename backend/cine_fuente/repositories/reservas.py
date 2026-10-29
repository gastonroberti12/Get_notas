from datetime import timedelta

from cine_fuente.db import ejecutar_consulta, ejecutar_escritura


def consultar(sql, parametros=None):
    """Ejecuta una consulta de lectura en db.py."""
    return ejecutar_consulta(sql, parametros or {})


def escribir(sql, parametros=None):
    """Ejecuta una escritura en db.py."""
    return ejecutar_escritura(sql, parametros or {})


def clausula_in(valores, prefijo):
    """Genera parámetros individuales para las butacas de POST /reservas."""
    nombres = [f"{prefijo}_{indice}" for indice in range(len(valores))]
    marcadores_parametros = ", ".join(f":{nombre}" for nombre in nombres)
    parametros = {nombre: valor for nombre, valor in zip(nombres, valores)}
    return marcadores_parametros, parametros