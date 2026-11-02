from datetime import datetime

from cine_fuente.utils import construir_error_api


# Valida fechas usadas por todos los GET /admin/estadisticas/*.
def error_fecha(campo):
    raise ValueError(
        construir_error_api(
            "fecha.invalid",
            "Fecha inválida",
            f"'{campo}' debe tener formato YYYY-MM-DD.",
        ),
        400,
    )


def validar_filtros_estadisticas(parametros):
    """Valida fecha_desde y fecha_hasta"""
    filtros = {}

    for campo in ("fecha_desde", "fecha_hasta"):
        valor = parametros.get(campo)
        if valor is None:
            filtros[campo] = None
            continue

        try:
            fecha = datetime.strptime(valor, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            error_fecha(campo)

        if fecha.isoformat() != valor:
            error_fecha(campo)
        filtros[campo] = fecha.isoformat()

    desde = filtros["fecha_desde"]
    hasta = filtros["fecha_hasta"]
    if desde is not None and hasta is not None and desde > hasta:
        raise ValueError(
            construir_error_api(
                "fecha.range.invalid",
                "Rango de fechas inválido",
                "'fecha_desde' no puede ser posterior a 'fecha_hasta'.",
            ),
            400,
        )

    return filtros