from cine_fuente.db import ejecutar_consulta


ESTADOS_VENTA = "'confirmada', 'finalizada'"


# Utilidad compartida por los siete GET /admin/estadisticas/*.
def filtro_fechas(columna, filtros):
    """Construye límites parametrizados; columna solo recibe constantes internas."""
    condiciones = []
    parametros = {}

    if filtros.get("fecha_desde") is not None:
        condiciones.append(f"{columna} >= %(fecha_desde)s")
        parametros["fecha_desde"] = filtros["fecha_desde"]

    if filtros.get("fecha_hasta") is not None:
        # Límite exclusivo para incluir todo el día fecha_hasta, incluso microsegundos.
        condiciones.append(
            f"{columna} < DATE_ADD(%(fecha_hasta)s, INTERVAL 1 DAY)"
        )
        parametros["fecha_hasta"] = filtros["fecha_hasta"]

    return (" AND " + " AND ".join(condiciones)) if condiciones else "", parametros


# Ejecuta las consultas de lectura de todos los endpoints de estadísticas.
def consulta(sql, parametros):
    filas = ejecutar_consulta(sql, parametros)
    return filas


# GET /admin/estadisticas/ocupacion/general: suma entradas vendidas y capacidad de las funciones del período.
def consultar_ocupacion_general(filtros):
    rango, parametros = filtro_fechas("f.fecha_hora", filtros)
    sql = f"""
        SELECT
            COALESCE(SUM(funciones.entradas_vendidas), 0) AS entradas_vendidas,
            COALESCE(SUM(funciones.capacidad_total), 0) AS capacidad_total
        FROM (
            SELECT
                f.id,
                COALESCE(capacidad.cantidad, 0) AS capacidad_total,
                COUNT(e.id) AS entradas_vendidas
            FROM funcion AS f
            LEFT JOIN (
                SELECT sala_id, COUNT(*) AS cantidad
                FROM butacas
                GROUP BY sala_id
            ) AS capacidad ON capacidad.sala_id = f.sala_id
            LEFT JOIN reservas AS r
                ON r.funcion_id = f.id
                AND r.estado IN ({ESTADOS_VENTA})
            LEFT JOIN entrada AS e ON e.reserva_id = r.id
            WHERE 1 = 1{rango}
            GROUP BY f.id, capacidad.cantidad
        ) AS funciones
    """
    filas = consulta(sql, parametros)
    return filas[0] if filas else {"entradas_vendidas": 0, "capacidad_total": 0}