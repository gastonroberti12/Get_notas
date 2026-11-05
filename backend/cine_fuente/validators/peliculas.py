import re
from datetime import datetime, timedelta, timezone

from cine_fuente.utils import construir_error_api


PATRON_FECHA_CARTELERA = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}-03:00$"
)


def parsear_fecha_cartelera(valor, campo):
    if not isinstance(valor, str) or not PATRON_FECHA_CARTELERA.fullmatch(valor):
        raise ValueError(construir_error_api(
            "pelicula.fecha.formato",
            "Formato de fecha inválido",
            f"{campo} debe tener formato YYYY-MM-DDTHH:MM:SS.ffffff-03:00.",
        ), 400)

    try:
        fecha = datetime.fromisoformat(valor)
    except ValueError as error:
        raise ValueError(construir_error_api(
            "pelicula.fecha.formato",
            "Formato de fecha inválido",
            f"{campo} contiene una fecha inexistente.",
        ), 400) from error

    if fecha.utcoffset() != timedelta(hours=-3):
        raise ValueError(construir_error_api(
            "pelicula.fecha.zona",
            "Zona horaria inválida",
            f"{campo} debe estar expresada en GMT-3.",
        ), 400)
    return fecha


def validar_rango_cartelera(inicio, fin):
    inicio_dt = parsear_fecha_cartelera(inicio, "fecha_inicio_cartelera")
    fin_dt = parsear_fecha_cartelera(fin, "fecha_fin_cartelera")

    if fin_dt < inicio_dt:
        raise ValueError(construir_error_api(
            "pelicula.fecha.rango",
            "Rango de fechas inválido",
            "fecha_fin_cartelera debe ser posterior a fecha_inicio_cartelera.",
        ), 400)

    if fin_dt - inicio_dt > timedelta(days=7):
        raise ValueError(construir_error_api(
            "pelicula.fecha.extension",
            "Cartelera demasiado extensa",
            "La cartelera puede durar como máximo una semana.",
        ), 400)

    return inicio, fin


def convertir_fecha_existente(valor):
    if isinstance(valor, datetime):
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone(timedelta(hours=-3)))
        return valor.isoformat(timespec="microseconds")
    return valor


# Lee los filtros disponibles para las películas.
def validar_filtros(parametros):
    activa = parametros.get("activa")
    if activa not in (None, "true", "false"):
        raise ValueError(construir_error_api(
            "invalid.activa.format", "Formato inválido", "activa debe ser true o false."), 400)
    return {"sucursal_id": parametros.get("sucursal_id", type=int),
            "activa": None if activa is None else activa == "true"}