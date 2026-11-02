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