from cine_fuente.validators.comunes import validar_rango_fechas


# Valida fechas usadas por todos los GET /admin/estadisticas/*.
def validar_filtros_estadisticas(parametros):
    """Valida fecha_desde y fecha_hasta"""
    return validar_rango_fechas(parametros)
