from cine_fuente.db import ejecutar_consulta, ejecutar_escritura
from constants import CAMPOS_SERVICIOS_PERMITIDOS


# Auxiliar para construir filtros de servicios
def construir_filtros_servicios(nombre=None, activo=None):

    condiciones = []
    params = {}

    if nombre:
        condiciones.append("LOWER(nombre) LIKE LOWER(%(nombre)s)")
        params["nombre"] = f"%{nombre}%"

    if activo is not None:
        condiciones.append("activo = %(activo)s")
        params["activo"] = activo

    where = " WHERE " + " AND ".join(condiciones) if condiciones else ""

    return where, params


# GET /servicios - Listar servicios con filtros y paginación
def consultar_servicios(nombre=None, activo=None, limit=10, offset=0):

    where, params = construir_filtros_servicios(nombre, activo)

    sql = f"""
        SELECT id, nombre, descripcion, precio, activo
        FROM servicios
        {where}
        ORDER BY id
        LIMIT %(limit)s OFFSET %(offset)s
    """

    params["limit"] = limit
    params["offset"] = offset

    return ejecutar_consulta(sql, params)


# Contar servicios para construir la paginación
def contar_servicios(nombre=None, activo=None):

    where, params = construir_filtros_servicios(nombre, activo)

    sql = f"""
        SELECT COUNT(*) AS total
        FROM servicios
        {where}
    """

    resultado = ejecutar_consulta(sql, params)

    return resultado[0]["total"]


# GET /servicios/<id>
def consultar_servicio_por_id(servicio_id):

    sql = """
        SELECT id, nombre, descripcion, precio, activo
        FROM servicios
        WHERE id = %(id)s
    """

    resultado = ejecutar_consulta(sql, {"id": servicio_id})

    return resultado[0] if resultado else None


# POST /servicios
def insertar_servicio(nombre, descripcion, precio, activo=True):

    sql = """
        INSERT INTO servicios (nombre, descripcion, precio, activo)
        VALUES (%(nombre)s, %(descripcion)s, %(precio)s, %(activo)s)
    """

    params = {
        "nombre": nombre,
        "descripcion": descripcion,
        "precio": precio,
        "activo": activo
    }

    return ejecutar_escritura(sql, params)


# Comprobar si existe un servicio, incluso inactivo
def existe_servicio(servicio_id):

    sql = """
        SELECT id
        FROM servicios
        WHERE id = %(id)s
        LIMIT 1
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


# Verificar si un servicio tiene reservas asociadas
def servicio_tiene_reservas(servicio_id):

    sql = """
        SELECT id
        FROM reserva_servicios
        WHERE servicio_id = %(id)s
        LIMIT 1
    """

    resultado = ejecutar_consulta(sql, {"id": servicio_id})

    return len(resultado) > 0


# DELETE /servicios/<id>
def eliminar_servicio(servicio_id):

    sql = """
        DELETE FROM servicios
        WHERE id = %(id)s
    """

    ejecutar_escritura(sql, {"id": servicio_id})


#obtiene duenio, estado y si está dentro de los 10 minutos. Esta es la que podríamos reemplazar si tu compañero ya tiene una equivalente.
def consultar_reserva_para_servicios(reserva_id):
    sql = """
        SELECT id, usuario_id, estado,
               fecha_compra + INTERVAL 10 MINUTE > NOW() AS vigente
        FROM reservas
        WHERE id = %(reserva_id)s
    """

    resultado = ejecutar_consulta(sql, {"reserva_id": reserva_id})
    return resultado[0] if resultado else None


# GET /reservas/<id_reserva>/servicios
def consultar_servicios_reserva(reserva_id):

    sql = """
        SELECT
            rs.id,
            rs.reserva_id,
            rs.servicio_id,
            s.nombre,
            s.descripcion,
            rs.cantidad,
            rs.precio_unitario,
            rs.cantidad * rs.precio_unitario AS subtotal
        FROM reserva_servicios rs
        JOIN servicios s
            ON rs.servicio_id = s.id
        WHERE rs.reserva_id = %(reserva_id)s
        ORDER BY rs.id
    """

    return ejecutar_consulta(sql, {"reserva_id": reserva_id})


# servicio_reserva_id es reserva_servicios.id, no servicios.id.
# Verificar que un servicio reservado pertenece a una reserva.
def existe_servicio_en_reserva(reserva_id, servicio_reserva_id):

    sql = """
        SELECT id
        FROM reserva_servicios
        WHERE reserva_id = %(reserva_id)s
          AND id = %(servicio_reserva_id)s
        LIMIT 1
    """

    params = {
        "reserva_id": reserva_id,
        "servicio_reserva_id": servicio_reserva_id
    }

    resultado = ejecutar_consulta(sql, params)

    return len(resultado) > 0


# PATCH /reservas/<id_reserva>/servicios/<id_servicio>
def actualizar_cantidad_servicio_reserva(reserva_id, servicio_reserva_id, cantidad):

    sql = """
        UPDATE reserva_servicios
        SET cantidad = %(cantidad)s
        WHERE reserva_id = %(reserva_id)s
          AND id = %(servicio_reserva_id)s
    """

    params = {
        "reserva_id": reserva_id,
        "servicio_reserva_id": servicio_reserva_id,
        "cantidad": cantidad
    }

    ejecutar_escritura(sql, params)


# DELETE /reservas/<id_reserva>/servicios/<id_servicio>
def eliminar_servicio_reserva(reserva_id, servicio_reserva_id):

    sql = """
        DELETE FROM reserva_servicios
        WHERE reserva_id = %(reserva_id)s
          AND id = %(servicio_reserva_id)s
    """

    params = {
        "reserva_id": reserva_id,
        "servicio_reserva_id": servicio_reserva_id
    }

    ejecutar_escritura(sql, params)
