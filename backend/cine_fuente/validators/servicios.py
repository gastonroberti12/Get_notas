from decimal import Decimal, InvalidOperation

from cine_fuente.utils import construir_error_api


def error_validacion(descripcion):
    raise ValueError(construir_error_api(
        "ERROR_VALIDACION",
        "Datos inválidos",
        descripcion,
    ))


def validar_precio(valor):
    try:
        precio = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        error_validacion("El precio debe ser un número.")

    if precio < 0:
        error_validacion("El precio no puede ser negativo.")
    return float(precio)


def validar_creacion_servicio(datos):
    if not isinstance(datos, dict):
        error_validacion("El cuerpo de la solicitud debe ser un objeto JSON.")

    nombre = datos.get("nombre")
    if not isinstance(nombre, str) or not nombre.strip():
        error_validacion("El campo nombre es obligatorio.")

    campos = {
        "nombre": nombre.strip(),
        "descripcion": datos.get("descripcion", "").strip()
        if isinstance(datos.get("descripcion", ""), str)
        else "",
        "precio": validar_precio(datos.get("precio")),
        "activo": datos.get("activo", True),
    }
    if not isinstance(campos["activo"], bool):
        error_validacion("El campo activo debe ser true o false.")
    return campos


def validar_campos_servicio(datos):
    if not isinstance(datos, dict) or not datos:
        error_validacion("No se enviaron campos para modificar.")

    permitidos = {"nombre", "descripcion", "precio", "activo"}
    desconocidos = set(datos) - permitidos
    if desconocidos:
        error_validacion(
            "Campos no permitidos: " + ", ".join(sorted(desconocidos)) + "."
        )

    campos = dict(datos)
    if "nombre" in campos:
        if not isinstance(campos["nombre"], str) or not campos["nombre"].strip():
            error_validacion("El nombre no puede estar vacío.")
        campos["nombre"] = campos["nombre"].strip()
    if "descripcion" in campos:
        if not isinstance(campos["descripcion"], str):
            error_validacion("La descripción debe ser texto.")
        campos["descripcion"] = campos["descripcion"].strip()
    if "precio" in campos:
        campos["precio"] = validar_precio(campos["precio"])
    if "activo" in campos and not isinstance(campos["activo"], bool):
        error_validacion("El campo activo debe ser true o false.")
    return campos


def validar_modificacion_servicio_reserva(datos):
    if not isinstance(datos, dict) or "cantidad" not in datos:
        error_validacion("El campo cantidad es obligatorio.")

    cantidad = datos["cantidad"]
    if isinstance(cantidad, bool) or not isinstance(cantidad, int):
        error_validacion("La cantidad debe ser un número entero.")
    if cantidad <= 0:
        error_validacion("La cantidad debe ser mayor que cero.")
    return cantidad
