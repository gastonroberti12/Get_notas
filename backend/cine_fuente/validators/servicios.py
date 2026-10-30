from constants import CAMPOS_SERVICIOS_PERMITIDOS


# Validar nombre
def validar_nombre(nombre):

    if not isinstance(nombre, str) or not nombre.strip():
        raise ValueError("El nombre es obligatorio")

    nombre = nombre.strip()

    if len(nombre) > 100:
        raise ValueError("El nombre no puede superar los 100 caracteres")

    return nombre


# Validar descripción
def validar_descripcion(descripcion):

    if descripcion is None:
        return None

    if not isinstance(descripcion, str):
        raise ValueError("La descripción debe ser un texto")

    descripcion = descripcion.strip()

    if len(descripcion) > 255:
        raise ValueError("La descripción no puede superar los 255 caracteres")

    return descripcion or None


# Validar precio (entero en centavos según Swagger)
def validar_precio(precio):

    if type(precio) is not int:
        raise ValueError("El precio debe ser un número entero en centavos")

    if precio <= 0:
        raise ValueError("El precio debe ser mayor a cero")

    return precio


# Validar activo
def validar_activo(activo):

    if not isinstance(activo, bool):
        raise ValueError("El campo activo debe ser true o false")

    return activo


# Validar cantidad de servicios en una reserva
def validar_cantidad(cantidad):

    if type(cantidad) is not int:
        raise ValueError("La cantidad debe ser un número entero")

    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor a cero")

    return cantidad


# Validar campos enviados en PATCH /servicios/{id}
def validar_campos_servicio(datos):

    if not isinstance(datos, dict) or not datos:
        raise ValueError("No se enviaron datos válidos")

    validadores = {
        "nombre": validar_nombre,
        "descripcion": validar_descripcion,
        "precio": validar_precio,
        "activo": validar_activo
    }

    campos = {}

    for campo, valor in datos.items():

        if campo not in CAMPOS_SERVICIOS_PERMITIDOS or campo not in validadores:
            raise ValueError(f"Campo no permitido: {campo}")

        campos[campo] = validadores[campo](valor)

    return campos


# Validar el cuerpo del POST /servicios usando los mismos validadores del PATCH.
#exige que estén nombre y precio, porque son obligatorios para crear un servicio
def validar_creacion_servicio(datos):
    campos = validar_campos_servicio(datos)

    if "nombre" not in campos or "precio" not in campos:
        raise ValueError("El nombre y el precio son obligatorios")

    if "descripcion" not in campos:
        campos["descripcion"] = None

    if "activo" not in campos:
        campos["activo"] = True

    return campos


# En una reserva solamente se puede modificar la cantidad del servicio.
def validar_modificacion_servicio_reserva(datos):
    if not isinstance(datos, dict):
        raise ValueError("Se debe enviar un objeto JSON")

    if "cantidad" not in datos or len(datos) != 1:
        raise ValueError("Se debe enviar únicamente el campo cantidad")

    return validar_cantidad(datos["cantidad"])




