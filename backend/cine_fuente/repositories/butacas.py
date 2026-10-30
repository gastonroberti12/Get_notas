from cine_fuente.db import ejecutar_consulta, ejecutar_escritura


# Consulta las butacas de una sala.
def consultar_butacas_por_sala(sala_id):
    return ejecutar_consulta(
        "SELECT id, sala_id, fila, numero FROM butacas WHERE sala_id = %s ORDER BY fila, numero",
        (sala_id,),
    )


# Busca una butaca por su identificador.
def consultar_butaca_por_id(butaca_id):
    filas = ejecutar_consulta(
        "SELECT id, sala_id, fila, numero FROM butacas WHERE id = %s", (butaca_id,),
    )
    return filas[0] if filas else None


# Obtiene varias butacas por sus identificadores.
def obtener_butacas(butaca_ids):
    if not butaca_ids:
        return []
    marcadores = ", ".join(["%s"] * len(butaca_ids))
    return ejecutar_consulta(
        f"SELECT id, sala_id, fila, numero FROM butacas WHERE id IN ({marcadores})",
        tuple(butaca_ids),
    )


# Guarda una nueva butaca.
def insertar_butaca(sala_id, fila, numero):
    return ejecutar_escritura(
        "INSERT INTO butacas (sala_id, fila, numero) VALUES (%s, %s, %s)",
        (sala_id, fila, numero),
    )


# Elimina una butaca.
def eliminar_butaca(butaca_id):
    ejecutar_escritura("DELETE FROM butacas WHERE id = %s", (butaca_id,),)


# Cuenta las butacas existentes en una sala.
def contar_butacas(sala_id):
    filas = ejecutar_consulta("SELECT COUNT(*) AS total FROM butacas WHERE sala_id = %s", (sala_id,),)
    return filas[0]["total"] if filas else 0


# Elimina todas las butacas de una sala.
def eliminar_butacas_de_sala(sala_id):
    ejecutar_escritura("DELETE FROM butacas WHERE sala_id = %s", (sala_id,),)
