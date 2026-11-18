from constants import CAMPOS_SERVICIOS_PERMITIDOS
from functools import partial
from cine_fuente.utils import validar_precio
from cine_fuente.validators.comunes import error_validacion, validar_campos, validar_texto

def validar_nombre(nombre):
    return validar_texto(nombre, "nombre", 100)


# Validar descripción (opcional: None o texto vacío se guardan como None)
def validar_descripcion(descripcion):

    if descripcion is None:
        return None

    if isinstance(descripcion, str) and not descripcion.strip():
        return None

    return validar_texto(descripcion, "descripcion", 255)


# Validar activo
def validar_activo(activo):

    if not isinstance(activo, bool):
        error_validacion("Valor invalido", "El campo activo debe ser true o false")

    return activo


# Validar cantidad de servicios en una reserva
def validar_cantidad(cantidad):

    if type(cantidad) is not int:
        error_validacion("Cantidad invalida", "La cantidad debe ser un numero entero")

    if cantidad <= 0:
        error_validacion("Cantidad invalida", "La cantidad debe ser mayor a cero")
    return cantidad


# Validar campos enviados en PATCH /servicios/{id}
def validar_campos_servicio(datos):

    if not isinstance(datos, dict) or not datos:
        error_validacion("Cuerpo JSON invalido", "No se enviaron datos validos")

    validadores = {
        "nombre": validar_nombre,
        "descripcion": validar_descripcion,
        "precio": partial(validar_precio, minimo=0),
        "activo": validar_activo
    }

    campos = {}

    for campo, valor in datos.items():

        if campo not in CAMPOS_SERVICIOS_PERMITIDOS or campo not in validadores:
            error_validacion("Campo no permitido", f"Campo no permitido: {campo}")

        campos[campo] = validadores[campo](valor)

    return campos


# Validar el cuerpo del POST /servicios usando los mismos validadores del PATCH.
#exige que estén nombre y precio, porque son obligatorios para crear un servicio
def validar_creacion_servicio(datos):
    campos = validar_campos_servicio(datos)

    if "nombre" not in campos or "precio" not in campos:
        error_validacion("Campos obligatorios faltantes", "El nombre y el precio son obligatorios")

    if "descripcion" not in campos:
        campos["descripcion"] = None

    if "activo" not in campos:
        campos["activo"] = True

    return campos


# En una reserva solamente se puede modificar la cantidad del servicio.
def validar_modificacion_servicio_reserva(datos):
    validar_campos(
        datos,
        {"cantidad"},
        {"cantidad"},
        error_cuerpo=("Cuerpo JSON invalido", "Se debe enviar un objeto JSON"),
        error_desconocidos=("Campos invalidos", "Se debe enviar únicamente el campo cantidad"),
        error_faltantes=("Campos invalidos", "Se debe enviar únicamente el campo cantidad"),
    )
    return validar_cantidad(datos["cantidad"])
