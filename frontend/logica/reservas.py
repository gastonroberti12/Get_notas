from datetime import timedelta
from logica.formato import SIN_DATO, ahora_argentina, formatear_fecha, formatear_numero, parsear_fecha

#reglas para definir como se muestran las reservas en el perfil,
# el estado de cada entrada y si todavía se puede cancelar.

ESTADOS_PROXIMAS = ('confirmada',)
ESTADOS_HISTORIAL = ('finalizada', 'cancelada')
TOLERANCIA_INGRESO_MIN_DEFAULT = 15
HORAS_MINIMAS_CANCELACION = 1


def funcion_termino_tolerancia(reserva):
    # True si ya pasó el horario para entrar a la función (inicio + tolerancia).
    inicio = parsear_fecha(reserva.get('fecha_hora'))
    if inicio is None:
        return False

    tolerancia = reserva.get('tolerancia_ingreso_min', TOLERANCIA_INGRESO_MIN_DEFAULT)
    try:
        tolerancia = int(tolerancia)
    except (TypeError, ValueError):
        tolerancia = TOLERANCIA_INGRESO_MIN_DEFAULT

    return ahora_argentina() > inicio + timedelta(minutes=tolerancia)


def clasificar_reserva(reserva):

    estado = reserva.get('estado')

    if estado in ESTADOS_HISTORIAL:
        return 'historial'

    if estado in ESTADOS_PROXIMAS:
        # si las entradas ya se usaron, no hay nada proximo, va al historial
        entradas = reserva.get('entradas', [])
        todas_usadas = bool(entradas) and all(e.get('fecha_uso') for e in entradas)

        if todas_usadas or funcion_termino_tolerancia(reserva):
            return 'historial'

        return 'proximas'
    return None


def estado_entrada(reserva, entrada, ingreso_vencido):

    if reserva['estado'] == 'cancelada':
        return 'cancelada'
    if entrada.get('fecha_uso'):
        return 'usada'
    if reserva['estado'] == 'confirmada' and not ingreso_vencido:
        return 'confirmada'
    if reserva['estado'] in ('confirmada', 'finalizada') and ingreso_vencido:
        return 'no_usada'
    return reserva['estado']


def armar_reserva(reserva):
    """Adapta una reserva del backend a lo que usa perfil.html: renombra campos, calcula el estado
    de cada entrada, separa fecha y hora, y decide si se puede cancelar."""
    ingreso_vencido = funcion_termino_tolerancia(reserva)

    entradas = []
    for entrada in reserva.get('entradas', []):
        entradas.append({
            'butaca': entrada.get('butaca', SIN_DATO),
            'codigo': entrada.get('codigo_qr'),
            'qr': entrada.get('qr_base64'),
            'usada': bool(entrada.get('fecha_uso')),
            'estado': estado_entrada(reserva, entrada, ingreso_vencido),
            'fecha_uso': formatear_fecha(entrada.get('fecha_uso'), '%d/%m/%Y %H:%M', None),
        })

    servicios = [f"{servicio['cantidad']} × {servicio['nombre']}" for servicio in reserva.get('servicios', [])]

    # si está confirmada y falta más de 1 hora se puede cancelar.
    inicio = parsear_fecha(reserva.get('fecha_hora'))
    faltan_mas_de_1h = inicio is not None and inicio - ahora_argentina() > timedelta(hours=HORAS_MINIMAS_CANCELACION)

    return {
        'id': reserva['id'],
        'estado': reserva['estado'],
        'pelicula': reserva.get('pelicula') or SIN_DATO,
        'pelicula_id': reserva.get('pelicula_id'),
        'poster': reserva.get('poster_url'),
        'fecha_funcion': formatear_fecha(reserva.get('fecha_hora'), '%d/%m/%Y'),
        'hora_funcion': formatear_fecha(reserva.get('fecha_hora'), '%H:%M'),
        'sucursal': reserva.get('sucursal') or SIN_DATO,
        'sala': reserva.get('sala') or SIN_DATO,
        'butacas': [entrada['butaca'] for entrada in entradas] or [SIN_DATO],
        'servicios': servicios,
        'total': formatear_numero(reserva['total']),
        'cancelable': reserva['estado'] == 'confirmada' and faltan_mas_de_1h,
        'entradas': entradas,
    }