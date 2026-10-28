from cine_fuente.db import ejecutar_consulta

def consultar_servicios():
    query = """
        SELECT id, nombre, descripcion, precio
        FROM servicios
        WHERE activo = TRUE
    """
    return ejecutar_consulta(query)

def consultar_servicio_por_id(servicio_id):
    query = """
        SELECT id, nombre, descripcion, precio
        FROM servicios
        WHERE id = :id AND activo = TRUE
    """

    resultados = ejecutar_consulta(query, {"id": servicio_id})

    return resultados[0] if resultados else None

from cine_fuente.db import ejecutar_escritura

def insertar_servicio(nombre, descripcion, precio):
    query = """
        INSERT INTO servicios (nombre, descripcion, precio)
        VALUES (:nombre, :descripcion, :precio)
    """

    params = {
        "nombre": nombre,
        "descripcion": descripcion,
        "precio": precio
    }

    return ejecutar_escritura(query, params)
