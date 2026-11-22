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
        # Límite exclusivo para incluir todo el día fecha_hasta.
        condiciones.append(
            f"{columna} < DATE_ADD(%(fecha_hasta)s, INTERVAL 1 DAY)"
        )
        parametros["fecha_hasta"] = filtros["fecha_hasta"]

    return (" AND " + " AND ".join(condiciones)) if condiciones else "", parametros


# Ejecuta las consultas de lectura de todos los endpoints de estadísticas.
def consulta(sql, parametros):
    filas = ejecutar_consulta(sql, parametros)
    return filas


def consultar_ocupacion_general(filtros):
    """GET /admin/estadisticas/ocupacion/general: devuelve un dict con entradas vendidas y capacidad del período."""
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


def consultar_ocupacion_salas(filtros):
    """GET /admin/estadisticas/ocupacion/salas: devuelve una lista de dict con entradas y capacidad por sala."""
    rango, parametros = filtro_fechas("f.fecha_hora", filtros)
    sql = f"""
        SELECT
            s.id AS sala_id,
            s.nombre AS sala_nombre,
            COALESCE(SUM(funciones.entradas_vendidas), 0) AS entradas_vendidas,
            COALESCE(SUM(funciones.capacidad_total), 0) AS capacidad_total
        FROM (
            SELECT
                f.id,
                f.sala_id,
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
            GROUP BY f.id, f.sala_id, capacidad.cantidad
        ) AS funciones
        INNER JOIN salas AS s ON s.id = funciones.sala_id
        GROUP BY s.id, s.nombre
        ORDER BY s.id ASC
    """
    return consulta(sql, parametros)


def consultar_franjas_horarias(filtros):
    """GET /admin/estadisticas/ocupacion/franjas_horarias: devuelve una lista de dict con entradas por hora de inicio."""
    rango, parametros = filtro_fechas("f.fecha_hora", filtros)
    sql = f"""
        SELECT
            HOUR(f.fecha_hora) AS hora,
            COUNT(e.id) AS entradas_vendidas
        FROM funcion AS f
        INNER JOIN reservas AS r
            ON r.funcion_id = f.id
            AND r.estado IN ({ESTADOS_VENTA})
        INNER JOIN entrada AS e ON e.reserva_id = r.id
        WHERE 1 = 1{rango}
        GROUP BY HOUR(f.fecha_hora)
        ORDER BY hora ASC
    """
    return consulta(sql, parametros)


def consultar_ventas_total(filtros):
    """GET /admin/estadisticas/ventas/total: devuelve un dict con importes de entradas y servicios (confirmadas/finalizadas)."""
    rango, parametros = filtro_fechas("r.fecha_compra", filtros)
    sql_entradas = f"""
        SELECT
            COUNT(e.id) AS entradas_vendidas,
            CAST(ROUND(COALESCE(SUM(f.precio * 100), 0), 0) AS SIGNED)
                AS monto_entradas
        FROM reservas AS r
        INNER JOIN funcion AS f ON f.id = r.funcion_id
        INNER JOIN entrada AS e ON e.reserva_id = r.id
        WHERE r.estado IN ({ESTADOS_VENTA}){rango}
    """
    entradas = consulta(sql_entradas, parametros)

    sql_servicios = f"""
        SELECT
            CAST(ROUND(
                COALESCE(SUM(rs.cantidad * rs.precio_unitario * 100), 0),
                0
            ) AS SIGNED) AS monto_servicios
        FROM reservas AS r
        INNER JOIN reserva_servicios AS rs ON rs.reserva_id = r.id
        WHERE r.estado IN ({ESTADOS_VENTA}){rango}
    """
    servicios = consulta(sql_servicios, parametros)

    return {
        **(entradas[0] if entradas else {}),
        **(servicios[0] if servicios else {}),
    }


def consultar_ventas_generos(filtros):
    """GET /admin/estadisticas/ventas/generos: devuelve una lista de dict con cantidad e importe por género."""
    rango, parametros = filtro_fechas("r.fecha_compra", filtros)
    sql = f"""
        SELECT
            COALESCE(NULLIF(TRIM(p.genero), ''), 'Sin especificar') AS genero,
            COUNT(e.id) AS entradas_vendidas,
            CAST(ROUND(COALESCE(SUM(f.precio * 100), 0), 0) AS SIGNED)
                AS monto_total
        FROM reservas AS r
        INNER JOIN funcion AS f ON f.id = r.funcion_id
        INNER JOIN pelicula AS p ON p.id = f.pelicula_id
        INNER JOIN entrada AS e ON e.reserva_id = r.id
        WHERE r.estado IN ({ESTADOS_VENTA}){rango}
        GROUP BY COALESCE(NULLIF(TRIM(p.genero), ''), 'Sin especificar')
        ORDER BY monto_total DESC, genero ASC
    """
    return consulta(sql, parametros)


def consultar_ventas_peliculas(filtros):
    """GET /admin/estadisticas/ventas/peliculas: devuelve una lista de dict con cantidad e importe por película."""
    rango, parametros = filtro_fechas("r.fecha_compra", filtros)
    sql = f"""
        SELECT
            p.id AS pelicula_id,
            p.titulo,
            COUNT(e.id) AS entradas_vendidas,
            CAST(ROUND(COALESCE(SUM(f.precio * 100), 0), 0) AS SIGNED)
                AS monto_total
        FROM reservas AS r
        INNER JOIN funcion AS f ON f.id = r.funcion_id
        INNER JOIN pelicula AS p ON p.id = f.pelicula_id
        INNER JOIN entrada AS e ON e.reserva_id = r.id
        WHERE r.estado IN ({ESTADOS_VENTA}){rango}
        GROUP BY p.id, p.titulo
        ORDER BY monto_total DESC, p.titulo ASC
    """
    return consulta(sql, parametros)


def consultar_cancelaciones(filtros):
    """GET /admin/estadisticas/cancelaciones: devuelve un dict con reservas del período y cuántas se cancelaron."""
    rango, parametros = filtro_fechas("r.fecha_compra", filtros)
    sql = """
        SELECT
            COUNT(*) AS reservas_totales,
            SUM(CASE WHEN r.estado = 'cancelada' THEN 1 ELSE 0 END)
                AS reservas_canceladas,
            ROUND(
                100 * SUM(CASE WHEN r.estado = 'cancelada' THEN 1 ELSE 0 END)
                / NULLIF(COUNT(*), 0),
                1
            ) AS porcentaje_cancelacion
        FROM reservas AS r
        WHERE 1 = 1""" + rango
    filas = consulta(sql, parametros)
    return filas[0] if filas else {
        "reservas_totales": 0,
        "reservas_canceladas": 0,
        "porcentaje_cancelacion": 0,
    }
