from constants import CAMPOS_SERVICIOS_PERMITIDOS

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

def validar_activo(activo):
    if not isinstance(activo, bool):
        raise ValueError("El campo activo debe ser true o false")

    return activo


def validar_campos_servicio(datos): # devuelve los campos que se pasan en la request en un diccionario campo:valor ya validados

    if not isinstance(datos, dict) or not datos:
        raise ValueError("No se enviaron datos válidos")

    validadores = {     
        "nombre": validar_nombre,
        "descripcion": validar_descripcion,
        "precio": validar_precio,
        "activo": validar_activo
    }
    #es un diccionario donde los valores de las claves hacen referencia a las funciones, por eso va sin los () pq no la estamos ejecutando

    campos = {}

    for campo, valor in datos.items():

        if campo not in CAMPOS_SERVICIOS_PERMITIDOS:
            raise ValueError(f"Campo no permitido: {campo}")

        campos[campo] = validadores[campo](valor)
        # validadores["nombre"]("Pochoclos XL") equivale a validar_nombre("Pochoclos XL")

    return campos
