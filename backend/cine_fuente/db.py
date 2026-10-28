from sqlalchemy import create_engine, text
from .constants import DB_URL

# Motor de conexion compartido por toda la aplicacion.
# El pool de conexiones lo maneja SQLAlchemy automaticamente.
motor = create_engine(DB_URL, pool_pre_ping=True)


def ejecutar_consulta(sql: str, params: dict = None) -> list[dict]:
    """Ejecuta consulta SQL de lectura en BD"""
    with motor.connect() as conexion:
        resultado = conexion.execute(text(sql), params or {})
        return [dict(fila._mapping) for fila in resultado]


def ejecutar_escritura(sql: str, params: dict = None) -> int:
    """Ejecuta consulta SQL de escritura en BD"""
    with motor.begin() as conexion:
        resultado = conexion.execute(text(sql), params or {})
        return resultado.lastrowid
