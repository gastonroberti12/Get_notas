from cine_fuente.db import ejecutar_consulta, ejecutar_escritura, ejecutar_transaccion
from cine_fuente.utils import construir_error_api


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


# Actualiza los datos identificatorios de una butaca.
def actualizar_butaca(butaca_id, datos):
    campos = ", ".join(f"{campo} = %s" for campo in datos)
    ejecutar_escritura(
        f"UPDATE butacas SET {campos} WHERE id = %s",
        (*datos.values(), butaca_id),
    )


# Elimina una butaca.
def eliminar_butaca(butaca_id):
    ejecutar_escritura("DELETE FROM butacas WHERE id = %s", (butaca_id,),)


# Cuenta las butacas existentes en una sala.
def contar_butacas(sala_id):
    filas = ejecutar_consulta("SELECT COUNT(*) AS total FROM butacas WHERE sala_id = %s", (sala_id,),)
    return filas[0]["total"] if filas else 0


def generar_butacas_atomico(sala_id):
    """Crea las butacas de una sala en una transacción, 10 por fila. Devuelve cuántas creó."""
    # Se define adentro para pasarla a ejecutar_transaccion, que hace commit/rollback.
    def operacion(cursor):
        # FOR UPDATE: bloquea la sala para que dos pedidos no generen butacas a la vez.
        cursor.execute(
            "SELECT capacidad FROM salas WHERE id = %s FOR UPDATE",
            (sala_id,),
        )
        sala = cursor.fetchone()
        if sala is None:
            raise ValueError(construir_error_api(
                "sala.not.found",
                "Sala no encontrada",
                "La sala solicitada no existe.",
            ), 404)

        capacidad = sala["capacidad"]
        if capacidad % 10 != 0:
            raise ValueError(construir_error_api(
                "sala.capacidad.invalid",
                "Capacidad inválida",
                "La capacidad debe ser múltiplo de 10 para generar butacas.",
            ), 400)

        cursor.execute(
            "SELECT COUNT(*) AS total FROM butacas WHERE sala_id = %s",
            (sala_id,),
        )
        if cursor.fetchone()["total"] != 0:
            raise ValueError(construir_error_api(
                "butacas.already.generated",
                "Butacas ya generadas",
                "La sala ya tiene butacas generadas.",
            ), 409)

        cantidad = capacidad
        for fila_numero in range(1, capacidad // 10 + 1):
            # 1 -> "A", 2 -> "B"...
            fila = chr(64 + fila_numero)
            for numero in range(1, 11):
                cursor.execute(
                    "INSERT INTO butacas (sala_id, fila, numero) VALUES (%s, %s, %s)",
                    (sala_id, fila, numero),
                )
        return cantidad

    return ejecutar_transaccion(operacion)


# Elimina todas las butacas de una sala.
def eliminar_butacas_de_sala(sala_id):
    ejecutar_escritura("DELETE FROM butacas WHERE sala_id = %s", (sala_id,),)
