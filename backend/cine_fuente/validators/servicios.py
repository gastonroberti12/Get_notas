
def validar_id_servicio(servicio_id):
    return servicio_id > 0


from decimal import Decimal, InvalidOperation


def validar_nombre(nombre):
    if not isinstance(nombre, str) or not nombre.strip():
        raise ValueError("El nombre es obligatorio")

    nombre = nombre.strip()

    if len(nombre) > 100:
        raise ValueError("El nombre no puede superar los 100 caracteres")

    return nombre


def validar_descripcion(descripcion):
    if descripcion is None:
        return None

    if not isinstance(descripcion, str):
        raise ValueError("La descripción debe ser un texto")

    descripcion = descripcion.strip()

    if len(descripcion) > 255:
        raise ValueError("La descripción no puede superar los 255 caracteres")

    return descripcion or None

def validar_precio(precio):
    if precio is None or isinstance(precio, bool):
        raise ValueError("El precio es obligatorio y debe ser numérico")

    try:
        precio = Decimal(str(precio))
    except (InvalidOperation, ValueError):
        raise ValueError("El precio debe ser numérico")

    if not precio.is_finite() or precio <= 0:
        raise ValueError("El precio debe ser mayor a cero")

    if precio > Decimal("99999999.99"):
        raise ValueError("El precio supera el máximo permitido")

    if precio != precio.quantize(Decimal("0.01")):
        raise ValueError("El precio debe tener como máximo dos decimales")

    return precio
