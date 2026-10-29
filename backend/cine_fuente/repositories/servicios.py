from cine_fuente.db import ejecutar_consulta, ejecutar_escritura
from constants import CAMPOS_SERVICIOS_PERMITIDOS


# GET /servicios
def consultar_servicios():
    sql = """
        SELECT id, nombre, descripcion, precio
        FROM servicios
        WHERE activo = TRUE
    """

    return ejecutar_consulta(sql)


# GET /servicios/<id>
def consultar_servicio_por_id(servicio_id):
    sql = """
        SELECT id, nombre, descripcion, precio
        FROM servicios
        WHERE id = %(id)s AND activo = TRUE
    """

    resultado = ejecutar_consulta(sql, {"id": servicio_id})

    return resultado[0] if resultado else None


# POST /servicios
def insertar_servicio(nombre, descripcion, precio):
    sql = """
        INSERT INTO servicios (nombre, descripcion, precio)
        VALUES (%(nombre)s, %(descripcion)s, %(precio)s)
    """

    params = {
        "nombre": nombre,
        "descripcion": descripcion,
        "precio": precio
    }

    return ejecutar_escritura(sql, params)


# Comprobar existencia, incluso si está inactivo
def existe_servicio(servicio_id):
    sql = """
        SELECT id
        FROM servicios
        WHERE id = %(id)s
    """

    resultado = ejecutar_consulta(sql, {"id": servicio_id})

    return len(resultado) > 0


# PATCH /servicios/<id>
def actualizar_servicio(servicio_id, campos):

    if not campos:
        raise ValueError("No hay campos para actualizar")

    for campo in campos:
        if campo not in CAMPOS_SERVICIOS_PERMITIDOS:
            raise ValueError(f"Campo no permitido: {campo}")

    modificaciones = ", ".join(
        f"{campo} = %({campo})s" for campo in campos
    )

    sql = f"""
        UPDATE servicios
        SET {modificaciones}
        WHERE id = %(id)s
    """

    params = {**campos, "id": servicio_id}

    ejecutar_escritura(sql, params)
