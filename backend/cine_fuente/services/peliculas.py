import pymysql
from datetime import datetime

from cine_fuente.repositories.peliculas import (
    actualizar_pelicula,
    consultar_pelicula_por_id,
    consultar_pelicula_por_imdb,
    consultar_peliculas,
    insertar_pelicula,
    tiene_reservas_activas,
)
from cine_fuente.services.omdb_service import obtener_detalle_pelicula
from cine_fuente.utils import construir_error_api, formatear_fecha_hora
from cine_fuente.validators.peliculas import (
    convertir_fecha_existente,
    parsear_fecha_cartelera,
    validar_inicio_no_pasado,
    validar_rango_cartelera,
)


# Lista las películas; con sucursal, solo las que tienen funciones futuras ahí.
def obtener_peliculas(filtros):
    return consultar_peliculas(
        activa=filtros["activa"],
        sucursal_id=filtros["sucursal_id"],
        titulo=filtros["titulo"],
        genero=filtros["genero"],
    )


def obtener_pelicula_por_id(pelicula_id):
    pelicula = consultar_pelicula_por_id(pelicula_id)
    return formatear_pelicula(pelicula) if pelicula is not None else None


def insertar_pelicula_segura(datos):
    datos = dict(datos)
    _normalizar_fechas_para_bd(datos)
    try:
        return insertar_pelicula(datos)
    except pymysql.err.IntegrityError as error:
        if error.args and error.args[0] == 1062:
            raise ValueError(construir_error_api(
                "pelicula.already.exists",
                "Película duplicada",
                "La película ya existe en la cartelera.",
            ), 409) from error
        raise


def crear_pelicula_desde_omdb(imdb_id, fecha_inicio, fecha_fin):
    pelicula_existente = consultar_pelicula_por_imdb(imdb_id)
    if pelicula_existente is not None:
        mensaje = (
            "La película ya existe pero está dada de baja; "
            "reactivala desde el listado."
            if not pelicula_existente["activa"]
            else "La película ya existe en la cartelera."
        )
        raise ValueError(construir_error_api(
            "pelicula.already.exists",
            "Película duplicada",
            mensaje,
        ), 409)

    pelicula = obtener_detalle_pelicula(imdb_id)
    pelicula.update({
        "fecha_inicio_cartelera": fecha_inicio,
        "fecha_fin_cartelera": fecha_fin,
        "activa": True,
    })
    pelicula_id = insertar_pelicula_segura(pelicula)
    pelicula_creada = obtener_pelicula_por_id(pelicula_id)
    if pelicula_creada is None:
        raise RuntimeError(
            "La película se insertó, pero no se pudo recuperar desde la base de datos."
        )
    return pelicula_creada


def formatear_pelicula(fila):
    pelicula = dict(fila)
    pelicula["fecha_inicio_cartelera"] = formatear_fecha_hora(
        pelicula["fecha_inicio_cartelera"]
    )
    pelicula["fecha_fin_cartelera"] = formatear_fecha_hora(
        pelicula["fecha_fin_cartelera"]
    )
    pelicula["activa"] = bool(pelicula["activa"])
    return pelicula


def dar_de_baja(pelicula_id):
    if tiene_reservas_activas(pelicula_id):
        return False
    actualizar_pelicula(pelicula_id, {"activa": False})
    return True


def eliminar_pelicula(pelicula_id):
    if consultar_pelicula_por_id(pelicula_id) is None:
        raise ValueError(construir_error_api(
            "pelicula.not.found",
            "Película no encontrada",
            "La película solicitada no existe.",
        ), 404)
    if not dar_de_baja(pelicula_id):
        raise ValueError(construir_error_api(
            "BAJA_CON_RESERVAS_ACTIVAS",
            "No se puede dar de baja la película",
            "La película tiene reservas activas para funciones futuras.",
        ), 409)


def actualizar_pelicula_por_id(pelicula_id, cambios):
    pelicula_actual = consultar_pelicula_por_id(pelicula_id)
    if pelicula_actual is None:
        raise ValueError(construir_error_api(
            "pelicula.not.found",
            "Película no encontrada",
            "La película solicitada no existe.",
        ), 404)

    cambios = dict(cambios)
    if "fecha_inicio_cartelera" in cambios or "fecha_fin_cartelera" in cambios:
        fecha_inicio = convertir_fecha_existente(
            cambios.get(
                "fecha_inicio_cartelera",
                pelicula_actual["fecha_inicio_cartelera"],
            )
        )
        fecha_fin = convertir_fecha_existente(
            cambios.get(
                "fecha_fin_cartelera",
                pelicula_actual["fecha_fin_cartelera"],
            )
        )
        if fecha_inicio is not None or fecha_fin is not None:
            if fecha_inicio is None or fecha_fin is None:
                raise ValueError(construir_error_api(
                    "pelicula.fecha.required",
                    "Fechas requeridas",
                    "La película debe tener fecha de inicio y fecha de fin.",
                ), 400)
            validar_rango_cartelera(fecha_inicio, fecha_fin)
            inicio_enviado = "fecha_inicio_cartelera" in cambios
            reactivando = (
                cambios.get("activa") is True
                and not pelicula_actual["activa"]
            )
            if inicio_enviado:
                inicio_dt = parsear_fecha_cartelera(
                    convertir_fecha_existente(cambios["fecha_inicio_cartelera"]),
                    "fecha_inicio_cartelera",
                )
                inicio_guardado = parsear_fecha_cartelera(
                    convertir_fecha_existente(
                        pelicula_actual["fecha_inicio_cartelera"]
                    ),
                    "fecha_inicio_cartelera",
                )
                if reactivando or inicio_dt != inicio_guardado:
                    validar_inicio_no_pasado(inicio_dt)
        _normalizar_fechas_para_bd(cambios)

    if cambios.get("activa") is False:
        if not dar_de_baja(pelicula_id):
            raise ValueError(construir_error_api(
                "BAJA_CON_RESERVAS_ACTIVAS",
                "No se puede dar de baja la película",
                "La película tiene reservas activas para funciones futuras.",
            ), 409)
        cambios.pop("activa")
    elif cambios.get("activa") is True and not pelicula_actual["activa"]:
        if (
            "fecha_inicio_cartelera" not in cambios
            or "fecha_fin_cartelera" not in cambios
        ):
            raise ValueError(construir_error_api(
                "pelicula.fecha.required",
                "Fechas requeridas",
                "La reactivación requiere un nuevo período de cartelera.",
            ), 400)

    if cambios:
        actualizar_pelicula(pelicula_id, cambios)


def _normalizar_fechas_para_bd(datos):
    for campo in ("fecha_inicio_cartelera", "fecha_fin_cartelera"):
        valor = datos.get(campo)
        if valor is not None:
            if isinstance(valor, str):
                valor = datetime.fromisoformat(valor)
            datos[campo] = valor.replace(tzinfo=None)