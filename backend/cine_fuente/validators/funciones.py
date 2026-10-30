from datetime import datetime
from decimal import Decimal, InvalidOperation

from cine_fuente.utils import construir_error_api


# Valida la fecha y hora de una función.
def validar_fecha_hora(valor):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(construir_error_api("required.fecha_hora", "Campo requerido: 'fecha_hora'", "La fecha y hora son obligatorias."))
    try:
        return datetime.fromisoformat(valor.strip().replace("Z", "+00:00"))
    except ValueError as causa:
        raise ValueError(construir_error_api("invalid.fecha_hora.format", "Formato de fecha inválido", "fecha_hora debe tener formato ISO-8601.")) from causa


# Valida el precio de una función.
def validar_precio(valor):
    try:
        precio = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError) as causa:
        raise ValueError(construir_error_api("invalid.precio.format", "Formato de precio inválido", "precio debe ser un número.")) from causa
    if not precio.is_finite() or precio <= 0:
        raise ValueError(construir_error_api("invalid.precio.value", "Precio inválido", "precio debe ser mayor que cero."))
    return precio


# Lee los filtros disponibles para las funciones.
def validar_filtros(parametros):
    activa = None
    activa_texto = parametros.get("activa")
    if activa_texto is not None:
        if activa_texto.lower() not in {"true", "false"}:
            raise ValueError(construir_error_api("invalid.activa.format", "Formato inválido", "activa debe ser true o false."))
        activa = activa_texto.lower() == "true"
    return {
        "pelicula_id": parametros.get("pelicula_id", type=int),
        "sala_id": parametros.get("sala_id", type=int),
        "activa": activa,
    }


# Valida los datos necesarios para crear una función.
def validar_creacion(datos):
    if not isinstance(datos, dict):
        raise ValueError(construir_error_api("invalid.body", "Datos inválidos", "El cuerpo de la solicitud no es válido."))
    try:
        pelicula_id = int(datos["pelicula_id"])
        sala_id = int(datos["sala_id"])
        fecha_hora = validar_fecha_hora(datos["fecha_hora"])
        precio = validar_precio(datos["precio"])
    except KeyError as campo:
        raise ValueError(construir_error_api("invalid.body", "Datos incompletos", f"Falta el campo '{campo.args[0]}'.")) from campo
    except (TypeError, ValueError) as causa:
        respuesta = causa.args[0] if causa.args and isinstance(causa.args[0], dict) else construir_error_api("invalid.body", "Datos inválidos", "Los datos enviados no son válidos.")
        raise ValueError(respuesta) from causa
    return pelicula_id, sala_id, fecha_hora, precio


# Valida los datos enviados para modificar una función.
def validar_modificacion(datos):
    cambios = {}
    if "pelicula_id" in datos:
        try:
            cambios["pelicula_id"] = int(datos["pelicula_id"])
        except (TypeError, ValueError) as causa:
            raise ValueError(construir_error_api("invalid.pelicula_id.format", "Formato inválido", "pelicula_id debe ser un entero.")) from causa
    if "sala_id" in datos:
        try:
            cambios["sala_id"] = int(datos["sala_id"])
        except (TypeError, ValueError) as causa:
            raise ValueError(construir_error_api("invalid.sala_id.format", "Formato inválido", "sala_id debe ser un entero.")) from causa
    if "fecha_hora" in datos:
        cambios["fecha_hora"] = validar_fecha_hora(datos["fecha_hora"])
    if "precio" in datos:
        cambios["precio"] = validar_precio(datos["precio"])
    if "activa" in datos:
        if not isinstance(datos["activa"], bool):
            raise ValueError(construir_error_api("invalid.activa.format", "Formato inválido", "activa debe ser true o false."))
        cambios["activa"] = datos["activa"]
    if not cambios:
        raise ValueError(construir_error_api("invalid.body", "Datos inválidos", "No se enviaron campos para modificar."))
    return cambios
