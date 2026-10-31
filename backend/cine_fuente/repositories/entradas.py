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


def obtener_entrada_por_id(entrada_id):
    """Incluye los datos necesarios para comprobar titularidad y horario."""
    sql = """
        SELECT e.id, e.reserva_id, e.butaca_id, e.codigo_qr, e.fecha_uso,
               r.usuario_id, r.estado AS estado_reserva,
               f.fecha_hora, p.duracion_min
        FROM entrada AS e
        INNER JOIN reservas AS r ON r.id = e.reserva_id
        INNER JOIN funcion AS f ON f.id = r.funcion_id
        INNER JOIN pelicula AS p ON p.id = f.pelicula_id
        WHERE e.id = %(entrada_id)s
    """
    filas = ejecutar_consulta(sql, {"entrada_id": entrada_id})
    return filas[0] if filas else None
