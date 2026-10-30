from cine_fuente.db import ejecutar_consulta, ejecutar_escritura


# Consulta los servicios disponibles.
def consultar_servicios(incluir_inactivos=False):
    sql = "SELECT id, nombre, descripcion, precio, activo FROM servicios"
    params = None
    if not incluir_inactivos:
        sql += " WHERE activo = TRUE"
    sql += " ORDER BY nombre"
    return ejecutar_consulta(sql, params)


# Busca un servicio por su identificador.
def consultar_servicio_por_id(servicio_id):
    filas = ejecutar_consulta(
        "SELECT id, nombre, descripcion, precio, activo FROM servicios WHERE id = %s",
        (servicio_id,),
    )
    return filas[0] if filas else None


# Guarda un nuevo servicio.
def insertar_servicio(nombre, descripcion, precio):
    return ejecutar_escritura(
        "INSERT INTO servicios (nombre, descripcion, precio, activo) VALUES (%s, %s, %s, TRUE)",
        (nombre, descripcion, precio),
    )


# Modifica los datos de un servicio.
def actualizar_servicio(servicio_id, datos):
    campos = ", ".join(f"{campo} = %s" for campo in datos)
    ejecutar_escritura(f"UPDATE servicios SET {campos} WHERE id = %s", (*datos.values(), servicio_id))


# Marca un servicio como inactivo.
def desactivar_servicio(servicio_id):
    ejecutar_escritura("UPDATE servicios SET activo = FALSE WHERE id = %s", (servicio_id,),)
