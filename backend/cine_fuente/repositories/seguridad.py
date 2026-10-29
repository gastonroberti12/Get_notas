"""Consulta SQL para identificar al usuario desde un token Bearer."""

# Todos los endpoints protegidos de Reservas: esta consulta valida Authorization: Bearer <token>.

from cine_fuente.db import ejecutar_consulta


def obtener_usuario_por_token(token: str) -> dict | None:
    """Todos los endpoints protegidos de Reservas: obtiene al usuario asociado al token Bearer."""
    sql = """
        SELECT id, nombre, apellido, email, rol
        FROM usuarios
        WHERE token = :token
        LIMIT 1
    """
    filas = ejecutar_consulta(sql, {"token": token})
    return filas[0] if filas else None
