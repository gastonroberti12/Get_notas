from cine_fuente.utils import construir_error_api
from cine_fuente.validators.comunes import error_validacion, validar_texto


def _entero(valor, codigo, titulo, detalle):
    if type(valor) is int:
        return valor
    if isinstance(valor, str):
        try:
            return int(valor)
        except ValueError:
            pass
    raise ValueError(construir_error_api(codigo, titulo, detalle), 400)


def validar_creacion_sala(datos):
    if not isinstance(datos, dict):
        error_validacion(
            "Datos inválidos",
            "Se debe enviar un objeto JSON.",
            "invalid.body",
        )
    for campo in ("sucursal_id", "nombre", "capacidad"):
        if campo not in datos:
            error_validacion(
                "Datos incompletos",
                f"Falta el campo '{campo}'.",
                "invalid.body",
            )

    sucursal_id = _entero(
        datos["sucursal_id"],
        "invalid.body",
        "Datos inválidos",
        "sucursal_id y capacidad deben ser enteros.",
    )
    capacidad = _entero(
        datos["capacidad"],
        "invalid.body",
        "Datos inválidos",
        "sucursal_id y capacidad deben ser enteros.",
    )
    if capacidad < 1:
        error_validacion(
            "Capacidad inválida",
            "capacidad debe ser mayor que cero.",
            "invalid.capacidad.value",
        )
    nombre = validar_texto(datos["nombre"], "nombre", 50)
    return sucursal_id, nombre, capacidad


def validar_modificacion_sala(datos):
    if not isinstance(datos, dict):
        error_validacion(
            "Datos inválidos",
            "Se debe enviar un objeto JSON.",
            "invalid.body",
        )

    cambios = {}
    if "nombre" in datos:
        cambios["nombre"] = validar_texto(datos["nombre"], "nombre", 50)

    if "capacidad" in datos:
        capacidad = _entero(
            datos["capacidad"],
            "invalid.capacidad.value",
            "Capacidad inválida",
            "capacidad debe ser un entero mayor que cero.",
        )
        if capacidad < 1:
            error_validacion(
                "Capacidad inválida",
                "capacidad debe ser un entero mayor que cero.",
                "invalid.capacidad.value",
            )
        cambios["capacidad"] = capacidad

    if "sucursal_id" in datos:
        cambios["sucursal_id"] = _entero(
            datos["sucursal_id"],
            "invalid.sucursal_id.format",
            "Formato inválido",
            "sucursal_id debe ser un entero.",
        )

    if not cambios:
        error_validacion(
            "Datos inválidos",
            "No se enviaron campos para modificar.",
            "invalid.body",
        )
    return cambios
