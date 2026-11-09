import re
from datetime import datetime, timedelta, timezone

from cine_fuente.utils import construir_error_api
from cine_fuente.utils import ahora_gmt3


PATRON_FECHA_CARTELERA = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}-03:00$"
)
LONGITUDES_PELICULA = {
    "titulo": 200,
    "poster_url": 500,
    "clasificacion": 20,
    "genero": 100,
}


def error_pelicula(campo, mensaje):
    raise ValueError(construir_error_api(
        f"pelicula.{campo}.invalid",
        "Datos de película inválidos",
        mensaje,
    ), 400)


def validar_modificacion_pelicula(datos):
    if not isinstance(datos, dict) or not datos:
        error_pelicula("body", "Se debe enviar un objeto con campos para modificar.")

    permitidos = set(LONGITUDES_PELICULA) | {
        "sinopsis", "duracion_min", "fecha_inicio_cartelera",
        "fecha_fin_cartelera", "activa",
    }
    desconocidos = set(datos) - permitidos
    if desconocidos:
        error_pelicula(
            "campo",
            f"Campo(s) no permitido(s): {', '.join(sorted(desconocidos))}.",
        )

    cambios = {}
    for campo, valor in datos.items():
        if campo in LONGITUDES_PELICULA or campo == "sinopsis":
            if valor is not None and not isinstance(valor, str):
                error_pelicula(campo, f"{campo} debe ser un texto o null.")
            if campo == "titulo" and valor is None:
                error_pelicula(campo, "titulo es obligatorio.")
            if isinstance(valor, str):
                valor = valor.strip() or None
                if campo == "titulo" and valor is None:
                    error_pelicula(campo, "titulo es obligatorio.")
                maximo = LONGITUDES_PELICULA.get(campo)
                if maximo is not None and valor is not None and len(valor) > maximo:
                    error_pelicula(
                        campo,
                        f"{campo} no puede superar los {maximo} caracteres.",
                    )
        elif campo == "duracion_min":
            if valor is not None and (
                type(valor) is not int or valor <= 0
            ):
                error_pelicula(
                    campo,
                    "duracion_min debe ser un número entero mayor que cero o null.",
                )
        elif campo == "activa" and type(valor) is not bool:
            error_pelicula(campo, "activa debe ser true o false.")
        elif campo in ("fecha_inicio_cartelera", "fecha_fin_cartelera"):
            if valor is not None and not isinstance(valor, str):
                error_pelicula(campo, f"{campo} debe ser una fecha o null.")
            cambios[campo] = convertir_fecha_existente(valor)
            continue
        cambios[campo] = valor

    return cambios


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

    if fin_dt <= inicio_dt:
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


def validar_inicio_no_pasado(inicio):
    ahora = ahora_gmt3().replace(second=0, microsecond=0)
    if inicio < ahora:
        raise ValueError(construir_error_api(
            "pelicula.fecha.pasada",
            "Fecha de cartelera inválida",
            "fecha_inicio_cartelera no puede estar en el pasado.",
        ), 400)


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