from cine_fuente.db import ejecutar_consulta, obtener_conexion




def construir_filtros(filtros):
    condiciones = []
    parametros = {}

    if filtros["reserva_id"] is not None:
        condiciones.append("e.reserva_id = %(reserva_id)s")
        parametros["reserva_id"] = filtros["reserva_id"]

    if filtros["estado"] is not None:
        condiciones.append("r.estado = %(estado)s")
        parametros["estado"] = filtros["estado"]
        
    if filtros.get("usuario_id") is not None:
            condiciones.append("r.usuario_id = %(usuario_id)s")
            parametros["usuario_id"] = filtros["usuario_id"]

    where = " WHERE " + " AND ".join(condiciones) if condiciones else ""
    return where, parametros
    



def listar_entradas(filtros, limit, offset):
    where, parametros = construir_filtros(filtros)
    parametros.update({"limit": limit, "offset": offset})
    sql = f"""
        SELECT e.id, e.reserva_id, e.butaca_id, e.codigo_qr, e.fecha_uso
        FROM entrada AS e
        INNER JOIN reservas AS r ON r.id = e.reserva_id
        {where}
        ORDER BY e.id
        LIMIT %(limit)s OFFSET %(offset)s
    """
    return ejecutar_consulta(sql, parametros)


def contar_entradas(filtros):
    where, parametros = construir_filtros(filtros)
    sql = f"""
        SELECT COUNT(*) AS total
        FROM entrada AS e
        INNER JOIN reservas AS r ON r.id = e.reserva_id
        {where}
    """
    filas = ejecutar_consulta(sql, parametros)
    return int(filas[0]["total"])

SQL_ENTRADA = """
    SELECT e.id, e.reserva_id, e.butaca_id, e.codigo_qr, e.fecha_uso,
           r.usuario_id, r.estado AS estado_reserva,
           f.fecha_hora, p.duracion_min, p.titulo AS pelicula_titulo,
           s.nombre AS sala_nombre, b.fila, b.numero
    FROM entrada AS e
    INNER JOIN reservas AS r ON r.id = e.reserva_id
    INNER JOIN funcion AS f ON f.id = r.funcion_id
    INNER JOIN pelicula AS p ON p.id = f.pelicula_id
    INNER JOIN salas AS s ON s.id = f.sala_id
    INNER JOIN butacas AS b ON b.id = e.butaca_id
"""

def _una(where, params):
    filas = ejecutar_consulta(SQL_ENTRADA + where, params)
    return filas[0] if filas else None

def obtener_entrada_por_id(entrada_id):
    return _una(" WHERE e.id = %(v)s", {"v": entrada_id})

def obtener_entrada_por_codigo_qr(codigo_qr):
    return _una(" WHERE e.codigo_qr = %(v)s", {"v": codigo_qr})

def registrar_uso_entrada(entrada_id, codigo_qr, fecha_uso, tolerancia):
    """Solo registra un uso si la entrada sigue siendo válida al escribir."""
    sql = """
        UPDATE entrada AS e
        INNER JOIN reservas AS r ON r.id = e.reserva_id
        INNER JOIN funcion AS f ON f.id = r.funcion_id
        INNER JOIN pelicula AS p ON p.id = f.pelicula_id
        SET e.fecha_uso = %(fecha_uso)s
        WHERE e.id = %(entrada_id)s
          AND BINARY e.codigo_qr = BINARY %(codigo_qr)s
          AND e.fecha_uso IS NULL
          AND r.estado = 'confirmada'
          AND p.duracion_min > 0
          AND DATE_SUB(f.fecha_hora, INTERVAL %(tolerancia)s MINUTE) <= %(fecha_uso)s
          AND %(fecha_uso)s < DATE_ADD(f.fecha_hora, INTERVAL p.duracion_min MINUTE)
    """
    parametros = {
        "entrada_id": entrada_id,
        "codigo_qr": codigo_qr,
        "fecha_uso": fecha_uso,
        "tolerancia": tolerancia,
    }

    # ejecutar_escritura devuelve lastrowid, no las filas modificadas.
    # Aquí necesitamos rowcount para saber si este escaneo registró el uso.
    with obtener_conexion() as conexion, conexion.cursor() as cursor:
        cursor.execute(sql, parametros)
        registrada = cursor.rowcount == 1
    return registrada
