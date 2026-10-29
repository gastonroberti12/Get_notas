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


# GET /reservas, /usuarios/me/reservas y /reservas/{id}


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