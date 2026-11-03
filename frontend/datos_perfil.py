from datetime import datetime, timedelta, timezone
from api_cliente import llamar_api

ESTADOS_PROXIMAS = ('confirmada',)
ESTADOS_HISTORIAL = ('finalizada', 'cancelada')
SIN_DATO = '—'

def obtener(endpoint, cache):
    # Evita pedir la función devuelta a la API si ya se pidio antes
    # la primera llamada se guarda en cache, si otra reserva tiene la misma funcion, se fija en el cache y no vuelve a pedirla al backend
    if endpoint not in cache:
        status, cuerpo = llamar_api('GET', endpoint)
        cache[endpoint] = cuerpo if status == 200 else {}
    return cache[endpoint]

def formatear_total(centavos):
    return f"{int(centavos) // 100:,}".replace(',', '.')

def armar_reserva(r, cache):
    # Consulta los datos de la reserva
    funcion = obtener(f"/funciones/{r['funcion_id']}", cache)
    sala = obtener(f"/salas/{funcion['sala_id']}", cache) if funcion.get('sala_id') else {}
    sucursal = obtener(f"/sucursales/{sala['sucursal_id']}", cache) if sala.get('sucursal_id') else {}
    pelicula = obtener(f"/peliculas/{funcion['pelicula_id']}", cache) if funcion.get('pelicula_id') else {}

    # Mapa butaca_id -> "C7" (las entradas solo traen el id de la butaca)
    butacas = {butaca['id']: f"{butaca['fila']}{butaca['numero']}"
               for butaca in obtener(f"/salas/{sala['id']}/butacas?_limit=100", cache).get('butacas', [])} if sala.get('id') else {}

    entradas_api = obtener(f"/reservas/{r['id']}/entradas?_limit=100", cache).get('entradas', [])
    entradas = [{
        'butaca': butacas.get(entrada['butaca_id'], SIN_DATO),
        'fecha_uso': formatear_fecha(entrada.get('fecha_uso'), '%d/%m/%Y %H:%M', None),
    } for entrada in entradas_api]

    servicios = [f"{servicio['cantidad']} × {servicio['nombre']}"
                 for servicio in obtener(f"/reservas/{r['id']}/servicios", cache).get('servicios', [])]

    inicio = parsear_fecha(funcion.get('fecha_hora'))
    faltan_mas_de_1h = inicio is not None and inicio - datetime.now(timezone.utc) > timedelta(hours=1)

    return {
        'id': r['id'],
        'estado': r['estado'],
        'pelicula': pelicula.get('titulo') or funcion.get('pelicula') or SIN_DATO,
        'poster': pelicula.get('poster_url'),
        'fecha_funcion': formatear_fecha(funcion.get('fecha_hora'), '%d/%m/%Y'),
        'hora_funcion': formatear_fecha(funcion.get('fecha_hora'), '%H:%M'),
        'sucursal': sucursal.get('nombre', SIN_DATO),
        'sala': sala.get('nombre') or funcion.get('sala') or SIN_DATO,
        'butacas': [entrada['butaca'] for entrada in entradas] or [SIN_DATO],
        'servicios': servicios,
        'total': formatear_total(r['total']),
        'cancelable': r['estado'] == 'confirmada' and faltan_mas_de_1h,  # el back rechaza (409) si falta menos de 1h
        'entradas': entradas,
    }
    

def parsear_fecha(valor):
    try:
        return datetime.fromisoformat(valor)
    except (TypeError, ValueError):
        return None


def formatear_fecha(valor, formato, sin_dato=SIN_DATO):
    fecha = parsear_fecha(valor)
    return fecha.strftime(formato) if fecha else sin_dato