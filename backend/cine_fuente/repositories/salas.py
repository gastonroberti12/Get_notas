from cine_fuente.db import ejecutar_consulta, ejecutar_escritura


# Consulta las salas registradas.
def consultar_salas(sucursal_id=None):
    if sucursal_id is None:
        return ejecutar_consulta(
            "SELECT s.id, s.sucursal_id, su.nombre AS sucursal, s.nombre, s.capacidad "
            "FROM salas s JOIN sucursales su ON su.id = s.sucursal_id ORDER BY su.nombre, s.nombre"
        )
    return ejecutar_consulta(
        "SELECT s.id, s.sucursal_id, su.nombre AS sucursal, s.nombre, s.capacidad "
        "FROM salas s JOIN sucursales su ON su.id = s.sucursal_id "
        "WHERE s.sucursal_id = %s ORDER BY s.nombre",
        (sucursal_id,),
    )


# Busca una sala por su identificador.
def consultar_sala_por_id(sala_id):
    filas = ejecutar_consulta(
        "SELECT s.id, s.sucursal_id, su.nombre AS sucursal, s.nombre, s.capacidad "
        "FROM salas s JOIN sucursales su ON su.id = s.sucursal_id WHERE s.id = %s",
        (sala_id,),
    )
    return filas[0] if filas else None


# Guarda una nueva sala.
def insertar_sala(sucursal_id, nombre, capacidad):
    return ejecutar_escritura(
        "INSERT INTO salas (sucursal_id, nombre, capacidad) VALUES (%s, %s, %s)",
        (sucursal_id, nombre, capacidad),
    )


# Modifica los datos de una sala.
def actualizar_sala(sala_id, datos):
    campos = ", ".join(f"{campo} = %s" for campo in datos)
    ejecutar_escritura(f"UPDATE salas SET {campos} WHERE id = %s", (*datos.values(), sala_id))


# Elimina una sala.
def eliminar_sala(sala_id):
    ejecutar_escritura("DELETE FROM salas WHERE id = %s", (sala_id,),)
