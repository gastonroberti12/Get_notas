from cine_fuente.db import ejecutar_consulta, ejecutar_escritura


# Consulta las sucursales registradas.
def consultar_sucursales():
    return ejecutar_consulta("SELECT id, nombre, direccion, telefono FROM sucursales ORDER BY nombre")


# Busca una sucursal por su identificador.
def consultar_sucursal_por_id(sucursal_id):
    filas = ejecutar_consulta(
        "SELECT id, nombre, direccion, telefono FROM sucursales WHERE id = %s",
        (sucursal_id,),
    )
    return filas[0] if filas else None


# Guarda una nueva sucursal.
def insertar_sucursal(nombre, direccion, telefono):
    return ejecutar_escritura(
        "INSERT INTO sucursales (nombre, direccion, telefono) VALUES (%s, %s, %s)",
        (nombre, direccion, telefono),
    )


# Modifica los datos de una sucursal.
def actualizar_sucursal(sucursal_id, datos):
    campos = ", ".join(f"{campo} = %s" for campo in datos)
    ejecutar_escritura(
        f"UPDATE sucursales SET {campos} WHERE id = %s",
        (*datos.values(), sucursal_id),
    )


# Elimina una sucursal.
def eliminar_sucursal(sucursal_id):
    ejecutar_escritura("DELETE FROM sucursales WHERE id = %s", (sucursal_id,),)
