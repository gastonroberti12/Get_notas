from datetime import timedelta

from cine_fuente.db import ejecutar_consulta, ejecutar_escritura


def consultar(sql, parametros=None):
    """Ejecuta una consulta de lectura en db.py."""
    return ejecutar_consulta(sql, parametros or {})


def escribir(sql, parametros=None):
    """Ejecuta una escritura en db.py."""
    return ejecutar_escritura(sql, parametros or {})


def clausula_in(valores, prefijo):
    """Genera parámetros individuales para las butacas de POST /reservas."""
    nombres = [f"{prefijo}_{indice}" for indice in range(len(valores))]
    marcadores_parametros = ", ".join(f":{nombre}" for nombre in nombres)
    parametros = {nombre: valor for nombre, valor in zip(nombres, valores)}
    return marcadores_parametros, parametros


# GET /reservas, /usuarios/me/reservas, /reservas/{id} y /reservas/{id}/entradas


def listar_reservas(filtros, limit, offset, usuario_propio_id=None):
    """lista reservas con filtros y paginación."""
    condiciones = []
    parametros = {"limit": limit, "offset": offset}

    for campo in ("usuario_id", "funcion_id", "estado"):
        valor = filtros.get(campo)
        if valor is not None:
            condiciones.append(f"r.{campo} = :{campo}")
            parametros[campo] = valor

    if usuario_propio_id is not None:
        condiciones.append("r.usuario_id = :usuario_propio_id")
        parametros["usuario_propio_id"] = usuario_propio_id

    if filtros.get("fecha_desde") is not None:
        condiciones.append("DATE(r.fecha_compra) >= :fecha_desde")
        parametros["fecha_desde"] = filtros["fecha_desde"]

    if filtros.get("fecha_hasta") is not None:
        condiciones.append("DATE(r.fecha_compra) <= :fecha_hasta")
        parametros["fecha_hasta"] = filtros["fecha_hasta"]

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    sql = f"""
        SELECT r.id, r.usuario_id, r.funcion_id, r.fecha_compra, r.estado,
        r.fecha_cancelacion, r.total
        FROM reservas AS r
        {where}
        ORDER BY r.fecha_compra DESC, r.id DESC
        LIMIT :limit OFFSET :offset
    """
    return consultar(sql, parametros)


def contar_reservas(filtros, usuario_propio_id=None):
    """Cuenta registros para la paginación."""
    condiciones = []
    parametros = {}

    for campo in ("usuario_id", "funcion_id", "estado"):
        valor = filtros.get(campo)
        if valor is not None:
            condiciones.append(f"r.{campo} = :{campo}")
            parametros[campo] = valor

    if usuario_propio_id is not None:
        condiciones.append("r.usuario_id = :usuario_propio_id")
        parametros["usuario_propio_id"] = usuario_propio_id

    if filtros.get("fecha_desde") is not None:
        condiciones.append("DATE(r.fecha_compra) >= :fecha_desde")
        parametros["fecha_desde"] = filtros["fecha_desde"]

    if filtros.get("fecha_hasta") is not None:
        condiciones.append("DATE(r.fecha_compra) <= :fecha_hasta")
        parametros["fecha_hasta"] = filtros["fecha_hasta"]

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    filas = consultar(f"SELECT COUNT(*) AS total FROM reservas AS r {where}", parametros)
    return int(filas[0]["total"]) if filas else 0


def obtener_reserva_por_id(reserva_id):
    """Obtiene una reserva."""
    sql = """
        SELECT id, usuario_id, funcion_id, fecha_compra, estado, fecha_cancelacion, total
        FROM reservas
        WHERE id = :reserva_id
    """
    filas = consultar(sql, {"reserva_id": reserva_id})
    return filas[0] if filas else None


def listar_entradas_reserva(reserva_id, limit, offset):
    """GET /reservas/{id}/entradas: lista las entradas de la reserva con paginación."""
    sql = """
        SELECT id, reserva_id, butaca_id, codigo_qr, fecha_uso
        FROM entrada
        WHERE reserva_id = :reserva_id
        ORDER BY id ASC
        LIMIT :limit OFFSET :offset
    """
    return consultar(sql, {"reserva_id": reserva_id, "limit": limit, "offset": offset})


def contar_entradas_reserva(reserva_id):
    """GET /reservas/{id}/entradas: cuenta entradas para construir los enlaces de paginación."""
    filas = consultar(
        "SELECT COUNT(*) AS total FROM entrada WHERE reserva_id = :reserva_id",
        {"reserva_id": reserva_id},
    )
    return int(filas[0]["total"]) if filas else 0


# POST /reservas y /reservas/{id}/pago


def obtener_butacas_ocupadas(funcion_id, butaca_ids):
    """Comprueba si las butacas tienen entradas asociadas a esa función."""
    if not butaca_ids:
        return []

    placeholders, parametros_in = clausula_in(butaca_ids, "ocupada")
    sql = f"""
        SELECT e.butaca_id
        FROM entrada AS e
        INNER JOIN reservas AS r ON e.reserva_id = r.id
        WHERE r.funcion_id = :funcion_id
        AND e.butaca_id IN ({placeholders})
    """
    parametros = {"funcion_id": funcion_id}
    parametros.update(parametros_in)

    filas = consultar(sql, parametros)
    return [int(fila["butaca_id"]) for fila in filas]


def insertar_reserva(datos):
    """Inserta una reserva pendiente común a las butacas seleccionadas."""
    sql = """
        INSERT INTO reservas
            (usuario_id, funcion_id, fecha_compra, estado, fecha_cancelacion, total)
        VALUES
            (:usuario_id, :funcion_id, :fecha_compra, :estado, NULL, :total)
    """
    return escribir(sql, datos)


def insertar_entrada(reserva_id, butaca_id):
    """Inserta una entrada por butaca con código QR nulo."""
    sql = """
        INSERT INTO entrada (reserva_id, butaca_id, codigo_qr, fecha_uso)
        VALUES (:reserva_id, :butaca_id, NULL, NULL)
    """
    return escribir(sql, {"reserva_id": reserva_id, "butaca_id": butaca_id})


def eliminar_reserva_incompleta(reserva_id):
    """Elimina la fila recién creada si falló la creación de sus entradas."""
    return escribir("DELETE FROM reservas WHERE id = :reserva_id", {"reserva_id": reserva_id})


def obtener_entradas_para_pago(reserva_id):
    """Obtiene todas las entradas cuyos QR deben generarse."""
    sql = """
        SELECT id, reserva_id, butaca_id, codigo_qr, fecha_uso
        FROM entrada
        WHERE reserva_id = :reserva_id
        ORDER BY id ASC
    """
    return consultar(sql, {"reserva_id": reserva_id})


def actualizar_entrada_qr(entrada_id, codigo_qr):
    """Asigna un QR."""
    sql = """
        UPDATE entrada
        SET codigo_qr = :codigo_qr
        WHERE id = :entrada_id
    """
    return escribir(sql, {"codigo_qr": codigo_qr, "entrada_id": entrada_id})


def restaurar_entrada_pendiente(entrada_id):
    """Limpia el QR si falla la confirmación parcial del pago."""
    sql = """
        UPDATE entrada
        SET codigo_qr = NULL
        WHERE id = :entrada_id
    """
    return escribir(sql, {"entrada_id": entrada_id})


def obtener_datos_notificacion(reserva_id):
    """Obtiene email y datos necesarios para el comprobante y sus QR."""
    sql = """
        SELECT r.id, r.usuario_id, r.funcion_id, r.fecha_compra, r.estado, r.total,
        u.nombre, u.apellido, u.email
        FROM reservas AS r
        INNER JOIN usuarios AS u ON u.id = r.usuario_id
        WHERE r.id = :reserva_id
    """
    filas = consultar(sql, {"reserva_id": reserva_id})
    if not filas:
        return None

    datos = filas[0]
    datos["entradas"] = consultar(
        "SELECT id, butaca_id, codigo_qr FROM entrada WHERE reserva_id = :reserva_id ORDER BY id",
        {"reserva_id": reserva_id},
    )
    return datos


# PATCH /reservas/{id}

def obtener_fecha_funcion_de_reserva(reserva_id):
    """Obtiene la fecha de la función para validar la anticipación de cancelación."""
    sql = """
        SELECT f.fecha_hora
        FROM reservas AS r
        INNER JOIN funciones AS f ON f.id = r.funcion_id
        WHERE r.id = :reserva_id
    """
    filas = consultar(sql, {"reserva_id": reserva_id})
    return filas[0]["fecha_hora"] if filas else None


def actualizar_estado_reserva(reserva_id, estado, fecha_cancelacion=None):
    """Actualiza el estado de la reserva."""
    if estado == "cancelada":
        sql = """
            UPDATE reservas
            SET estado = :estado, fecha_cancelacion = :fecha_cancelacion
            WHERE id = :reserva_id
        """
        parametros = {
            "estado": estado,
            "fecha_cancelacion": fecha_cancelacion,
            "reserva_id": reserva_id,
        }
    else:
        sql = "UPDATE reservas SET estado = :estado WHERE id = :reserva_id"
        parametros = {"estado": estado, "reserva_id": reserva_id}
    return escribir(sql, parametros)


def restaurar_estado_reserva(reserva_id, estado, fecha_cancelacion=None):
    """Compensa una escritura parcial ante un error."""
    sql = """
        UPDATE reservas
        SET estado = :estado, fecha_cancelacion = :fecha_cancelacion
        WHERE id = :reserva_id
    """
    return escribir(sql, {
        "estado": estado,
        "fecha_cancelacion": fecha_cancelacion,
        "reserva_id": reserva_id,
    })


def eliminar_entradas_reserva(reserva_id):
    """PATCH /reservas/{id} y expiración: elimina entradas para liberar las butacas."""
    return escribir("DELETE FROM entrada WHERE reserva_id = :reserva_id", {"reserva_id": reserva_id})


# Expiración


def listar_reservas_vencidas(fecha_limite):
    """Lista reservas pendientes vencidas."""
    sql = """
        SELECT id
        FROM reservas
        WHERE estado = 'pendiente' AND fecha_compra <= :fecha_limite
        ORDER BY id
    """
    return consultar(sql, {"fecha_limite": fecha_limite})