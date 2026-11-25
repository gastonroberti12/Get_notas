from datetime import datetime, timedelta, timezone

ZONA_ARGENTINA = timezone(timedelta(hours=-3))
SIN_DATO = '—'
FORMATO_INPUT_FECHA = '%Y-%m-%dT%H:%M'  # formato de los <input type="datetime-local">


def ahora_argentina():
    return datetime.now(ZONA_ARGENTINA)

def parsear_fecha(valor):  # convierte el texto ISO del backend en datetime, si viene sin zona, le pone la argentina.
    try:
        fecha = datetime.fromisoformat(valor)
    except (TypeError, ValueError):
        return None
    if fecha.tzinfo is None:  #tzinfo es el atributo de un datetime que guarda en QUE zona horaria esta esa fecha
        fecha = fecha.replace(tzinfo=ZONA_ARGENTINA)
    return fecha

def formatear_fecha(valor, formato, sin_dato=SIN_DATO):
    fecha = parsear_fecha(valor)
    return fecha.strftime(formato) if fecha else sin_dato

def a_iso_gmt3(valor):
    # convierte el valor de un <input type="datetime-local"> al formato ISO con zona que pide el backend.
    fecha = parsear_fecha(valor)
    if fecha is None:
        return valor or ''
    return fecha.strftime('%Y-%m-%dT%H:%M:%S') + '-03:00'

def formatear_numero(valor, decimales=0):
    # formato argentino: 1234.5 -> "1.234,5"
    try:
        texto = f'{valor:,.{decimales}f}'
    except (TypeError, ValueError):
        return '0'
    return texto.replace(',', 'X').replace('.', ',').replace('X', '.')  # la X es un marcador temporal para intercambiar comas y puntos