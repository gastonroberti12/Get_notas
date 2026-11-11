from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

ESTADOS_PROXIMAS = ('confirmada',)
ESTADOS_HISTORIAL = ('finalizada', 'cancelada')
SIN_DATO = '—'


def formatear_total(pesos):
    try:
        monto = Decimal(str(pesos)).quantize(
            Decimal('1'), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError):
        monto = Decimal('0')

    return f"{monto:,}".replace(',', '.')


def parsear_fecha(valor):
    try:
        return datetime.fromisoformat(valor)
    except (TypeError, ValueError):
        return None

def funcion_ya_comenzo(fecha_hora):
    fecha = parsear_fecha(fecha_hora)

    if fecha is None:
        return False

    zona_argentina = timezone(timedelta(hours=-3))

    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=zona_argentina)

    return fecha <= datetime.now(zona_argentina)

def clasificar_reserva(reserva):
    estado = reserva.get("estado")

    if estado in ESTADOS_HISTORIAL:
        return "historial"

    if estado in ESTADOS_PROXIMAS:
        if funcion_ya_comenzo(reserva.get("fecha_hora")):
            return "historial"

        return "proximas"

    return None

def formatear_fecha(valor, formato, sin_dato=SIN_DATO):
    fecha = parsear_fecha(valor)
    return fecha.strftime(formato) if fecha else sin_dato


def armar_reserva(reserva):
    """Prepara los datos de una reserva para mostrarlos en el perfil."""

    entradas = []
    funcion_comenzada = funcion_ya_comenzo(reserva.get('fecha_hora'))

    for entrada in reserva.get('entradas', []):
        
        usada = bool(entrada.get('fecha_uso'))

        # Estado propio de cada entrada: el de la reserva no dice si se usó.
        if reserva['estado'] == 'cancelada':
            estado = 'cancelada'
        elif usada:
            estado = 'usada'
        elif reserva['estado'] == 'confirmada' and not funcion_comenzada:
            estado = 'confirmada'
        elif reserva['estado'] in ('confirmada', 'finalizada'):
            estado = 'no_usada'
        else:
            estado = reserva['estado']
            
        entradas.append({
            'butaca': entrada.get('butaca', SIN_DATO),
            'codigo': entrada.get('codigo_qr'),
            'usada': usada,
            'estado': estado,
            'fecha_uso': formatear_fecha(
                entrada.get('fecha_uso'),
                '%d/%m/%Y %H:%M',
                None
            )
        })

    servicios = []

    for servicio in reserva.get('servicios', []):
        servicios.append(
            f"{servicio['cantidad']} × {servicio['nombre']}"
        )

    #comprobar si puede cancelarse
    inicio = parsear_fecha(reserva.get('fecha_hora'))

    faltan_mas_de_1h = (
        inicio is not None
        and inicio - datetime.now(timezone.utc) > timedelta(hours=1)
    )

    return {
        'id': reserva['id'],
        'estado': reserva['estado'],
        'pelicula': reserva.get('pelicula') or SIN_DATO,
        'poster': reserva.get('poster_url'),
        'fecha_funcion': formatear_fecha(
            reserva.get('fecha_hora'), '%d/%m/%Y'
        ),
        'hora_funcion': formatear_fecha(
            reserva.get('fecha_hora'), '%H:%M'
        ),
        'sucursal': reserva.get('sucursal') or SIN_DATO,
        'sala': reserva.get('sala') or SIN_DATO,
        'butacas': [entrada['butaca'] for entrada in entradas] or [SIN_DATO],
        'servicios': servicios,
        'total': formatear_total(reserva['total']),
        'cancelable': reserva['estado'] == 'confirmada' and faltan_mas_de_1h,
        'entradas': entradas,
    }