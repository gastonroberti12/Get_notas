from datetime import datetime

from cine_fuente.validators.comunes import error_validacion


# Valida fechas usadas por todos los GET /admin/estadisticas/*.
def validar_filtros_estadisticas(parametros):
    """Valida fecha_desde y fecha_hasta"""
    filtros = {}

    for campo in ("fecha_desde", "fecha_hasta"):
        valor = parametros.get(campo)
        if valor is None:
            filtros[campo] = None

        else:
            try:
                fecha = datetime.strptime(valor, "%Y-%m-%d").date()
            except (TypeError, ValueError):
                error_validacion("Fecha inválida", f"'{campo}' debe tener formato YYYY-MM-DD.", "fecha.invalid")

            if fecha.isoformat() != valor:
                error_validacion("Fecha inválida", f"'{campo}' debe tener formato YYYY-MM-DD.", "fecha.invalid")
            filtros[campo] = fecha.isoformat()

    desde = filtros["fecha_desde"]
    hasta = filtros["fecha_hasta"]
    if desde is not None and hasta is not None and desde > hasta:
        error_validacion(
            "Rango de fechas inválido",
            "'fecha_desde' no puede ser posterior a 'fecha_hasta'.",
            "fecha.range.invalid",
        )

    return filtros