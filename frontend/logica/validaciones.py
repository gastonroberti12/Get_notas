import re

# validaciones de los datos que llegan en los formularios

CONTRASENIA_MINIMA = 8 
CONTRASENIA_MAXIMA = 128
SERVICIOS_POR_ENTRADA = 2
PATRON_IMDB_ID = r'tt\d+'   #formato del id de la pelicula en imdb


def validar_entero(texto, mensaje):
    texto = (texto or '').strip()
    if not texto.isdigit():
        return None, mensaje
    return int(texto), None


def validar_imdb_id(texto):
    texto = (texto or '').strip()
    if not re.fullmatch(PATRON_IMDB_ID, texto): #todo el id tiene que cumplir con el patron
        return None, 'El identificador de IMDb no es válido.'
    return texto, None


def validar_butacas(texto):
    # las butacas elegidas llegan como "12,13,14" en un campo oculto del formulario
    butaca_ids = []
    for valor in (texto or '').split(','):
        if not valor.strip():
            continue
        butaca_id, error = validar_entero(valor, 'Las butacas seleccionadas no son válidas.')
        if error:
            return None, error
        butaca_ids.append(butaca_id)
    if not butaca_ids:
        return None, 'Seleccioná al menos una butaca.'
    return butaca_ids, None


def validar_cantidades_servicios(formulario, cantidad_entradas):
    # los campos se llaman servicio_<id>. Se permiten hasta SERVICIOS_POR_ENTRADA unidades por entrada.
    maximo = cantidad_entradas * SERVICIOS_POR_ENTRADA
    cantidades = {}
    for clave, texto in formulario.items():
        if not clave.startswith('servicio_'):
            continue
        servicio_id, _ = validar_entero(clave.replace('servicio_', ''), 'La cantidad del servicio no es válida.')
        cantidad, _ = validar_entero(texto, 'La cantidad del servicio no es válida.')
        if servicio_id is None or cantidad is None:
            return None, 'La cantidad del servicio no es válida.'
        if servicio_id <= 0 or cantidad > maximo:
            return None, f'El máximo permitido es {maximo} unidades por servicio.'
        cantidades[servicio_id] = cantidad
    return cantidades, None


def validar_cambio_contrasenia(actual, nueva, repetir):
    if not actual or not nueva or not repetir:
        return None, 'Completá todos los campos.'
    if nueva != repetir:
        return None, 'La nueva contraseña y su repetición no coinciden.'
    if len(nueva) < CONTRASENIA_MINIMA or len(nueva) > CONTRASENIA_MAXIMA:
        return None, f'La nueva contraseña debe tener entre {CONTRASENIA_MINIMA} y {CONTRASENIA_MAXIMA} caracteres.'
    return nueva, None