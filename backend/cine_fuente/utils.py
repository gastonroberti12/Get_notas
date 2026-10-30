from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from flask import g, jsonify, request

from cine_fuente.repositories.seguridad import obtener_usuario_por_token


PARAMETRO_LIMIT = "_limit"
PARAMETRO_OFFSET = "_offset"
PAGINACION_LIMIT_DEFAULT = 10
PAGINACION_LIMIT_MINIMO = 1
PAGINACION_LIMIT_MAXIMO = 100
PAGINACION_OFFSET_DEFAULT = 0
PAGINACION_OFFSET_MINIMO = 0


def construir_error_api(code: str, message: str, description: str, level: str = "error") -> dict:
    """Construye el formato de error para cualquier endpoint."""
    return {
        "errors": [{
            "code": code,
            "message": message,
            "level": level,
            "description": description,
        }]
    }


def formatear_fecha_hora(valor):
    if valor is None:
        return None
    if isinstance(valor, str):
        try:
            valor = datetime.fromisoformat(valor)
        except ValueError:
            return valor

    zona_gmt3 = timezone(timedelta(hours=-3))
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=zona_gmt3)
    else:
        valor = valor.astimezone(zona_gmt3)

    return valor.strftime("%Y-%m-%dT%H:%M:%S.%f-03:00")


def ahora_gmt3() -> datetime:
    return datetime.now(timezone(timedelta(hours=-3)))


def error_paginacion(codigo: str, mensaje: str, descripcion: str) -> None:
    """Utilidad común: levanta un error JSON de validación para parámetros de paginación."""
    raise ValueError(construir_error_api(codigo, mensaje, descripcion), 400)


def validar_entero_estricto(valor, nombre: str) -> int:
    """Valida un entero para parámetros de query sin aceptar booleanos ni decimales."""
    if isinstance(valor, bool):
        error_paginacion(
            "ERROR_VALIDACION", "Parámetro inválido",
            f"'{nombre}' debe ser un número entero."
        )

    try:
        texto = str(valor).strip()
        if not texto or texto.lstrip("+-").isdigit() is False:
            raise ValueError
        return int(texto)
    except (TypeError, ValueError):
        error_paginacion(
            "ERROR_VALIDACION", "Parámetro inválido",
            f"'{nombre}' debe ser un número entero."
        )


def validar_minimo(valor: int, minimo: int, nombre: str) -> int:
    """Valida el límite inferior."""
    if valor < minimo:
        error_paginacion(
            "ERROR_VALIDACION", "Parámetro fuera de rango",
            f"'{nombre}' debe ser mayor o igual a {minimo}."
        )
    return valor


def validar_maximo(valor: int, maximo: int, nombre: str) -> int:
    """Valida el límite superior."""
    if valor > maximo:
        error_paginacion(
            "ERROR_VALIDACION", "Parámetro fuera de rango",
            f"'{nombre}' debe ser menor o igual a {maximo}."
        )
    return valor


def validar_paginacion(parametros) -> tuple[int, int]:
    """Lee y valida _limit/_offset."""
    limit_crudo = parametros.get(PARAMETRO_LIMIT, PAGINACION_LIMIT_DEFAULT)
    limit = validar_entero_estricto(limit_crudo, PARAMETRO_LIMIT)
    limit = validar_minimo(limit, PAGINACION_LIMIT_MINIMO, PARAMETRO_LIMIT)
    limit = validar_maximo(limit, PAGINACION_LIMIT_MAXIMO, PARAMETRO_LIMIT)

    offset_crudo = parametros.get(PARAMETRO_OFFSET, PAGINACION_OFFSET_DEFAULT)
    offset = validar_entero_estricto(offset_crudo, PARAMETRO_OFFSET)
    offset = validar_minimo(offset, PAGINACION_OFFSET_MINIMO, PARAMETRO_OFFSET)

    return limit, offset


def construir_links(
    url_base: str,
    parametros: dict,
    total: int,
    limit: int,
    offset: int
) -> dict:
    """Construye los enlaces HATEOAS de paginación y conserva los filtros originales."""
    ultimo_offset = ((total - 1) // limit) * limit if total > 0 else 0

    def enlace(nuevo_offset: int) -> dict:
        consulta = parametros.copy()
        consulta[PARAMETRO_LIMIT] = limit
        consulta[PARAMETRO_OFFSET] = nuevo_offset
        return {"href": f"{url_base}?{urlencode(consulta)}"}

    enlaces = {"_first": enlace(0)}

    if offset > 0:
        enlaces["_prev"] = enlace(min(max(offset - limit, 0), ultimo_offset))

    if offset + limit < total:
        enlaces["_next"] = enlace(offset + limit)

    enlaces["_last"] = enlace(ultimo_offset)

    return enlaces


def respuesta_paginada(
    clave: str,
    registros: list[dict],
    total: int,
    limit: int,
    offset: int
):
    """Arma la respuesta HTTP común de cualquier listado paginado.

    Devuelve 204 si ningún registro coincide con los filtros. Si el offset supera el
    total, devuelve 200 con una lista vacía y enlaces para volver a una página válida.
    """
    if total == 0:
        return "", 204

    enlaces = construir_links(
        request.base_url,
        request.args.to_dict(flat=True),
        total,
        limit,
        offset
    )

    return jsonify({clave: registros, "_links": enlaces}), 200


def construir_links_paginacion(total: int, limit: int, offset: int) -> dict:
    return construir_links(
        request.base_url,
        request.args.to_dict(flat=True),
        total,
        limit,
        offset
    )


def requiere_token(roles: tuple[str, ...] | None = None):
    """Protege cualquier endpoint de la API comprobando el token almacenado en usuarios."""
    roles_permitidos = tuple(roles or ())

    def decorador(funcion):
        def envoltura(*args, **kwargs):
            cabecera = request.headers.get("Authorization", "")
            partes = cabecera.split(None, 1)

            if (
                len(partes) != 2
                or partes[0].lower() != "bearer"
                or not partes[1].strip()
            ):
                return jsonify(construir_error_api(
                    "TOKEN_REQUERIDO",
                    "Autenticación requerida",
                    "Envíe un token válido mediante Authorization: Bearer <token>.",
                )), 401

            try:
                usuario = obtener_usuario_por_token(partes[1].strip())
            except Exception:
                return jsonify(construir_error_api(
                    "ERROR_INTERNO",
                    "Error interno del servidor",
                    "No se pudo validar la autenticación."
                )), 500

            if usuario is None:
                return jsonify(construir_error_api(
                    "TOKEN_INVALIDO",
                    "Token inválido",
                    "El token no corresponde a una sesión de usuario válida.",
                )), 401

            if roles_permitidos and usuario.get("rol") not in roles_permitidos:
                return jsonify(construir_error_api(
                    "ROL_NO_AUTORIZADO",
                    "Acceso denegado",
                    f"El endpoint requiere uno de estos roles: {', '.join(roles_permitidos)}.",
                )), 403

            g.usuario = usuario
            return funcion(*args, **kwargs)

        # Flask usa el nombre de la función para identificar cada endpoint.
        envoltura.__name__ = funcion.__name__
        envoltura.__doc__ = funcion.__doc__

        return envoltura

    return decorador
