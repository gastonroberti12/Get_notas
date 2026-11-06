from urllib.parse import urlencode

from api_cliente import llamar_api, mensaje_error

BASE = "/admin/estadisticas"
RUTAS = {
    "general": "/ocupacion/general",
    "salas": "/ocupacion/salas",
    "franjas": "/ocupacion/franjas_horarias",
    "ventas": "/ventas/total",
    "generos": "/ventas/generos",
    "cancelaciones": "/cancelaciones",
}
# Con estos estados el resto de las consultas fallaría igual: se corta y se reutiliza el error.
ESTADOS_FATALES = (None, 400, 401, 403)
def numero(valor, decimales=0):
    # Formato es-AR: 1.234,5
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def pesos(centavos):
    # El backend informa los montos en centavos.
    return "$ " + numero(centavos / 100)

def leer_filtros(args):
    # Solo normaliza; la validación del rango la hace el backend.
    return {c: args.get(c, "").strip() or None for c in ("fecha_desde", "fecha_hasta")}


def consultar(filtros, endpoints):
    """Llama a cada endpoint por separado: si uno falla, los demás siguen mostrándose."""
    query = urlencode({k: v for k, v in filtros.items() if v})
    sufijo = f"?{query}" if query else ""
    respuestas, error_fatal = {}, None
    for clave in endpoints:
        if error_fatal:
            respuestas[clave] = (None, error_fatal)
            continue
        status, cuerpo = llamar_api("GET", BASE + RUTAS[clave] + sufijo)
        if status == 200:
            respuestas[clave] = (cuerpo, None)
            continue
        error = mensaje_error(status, cuerpo, "No se pudo cargar esta estadística.")
        respuestas[clave] = (None, error)
        if status in ESTADOS_FATALES:
            error_fatal = error
    return respuestas


def barras(filas, etiqueta, valor, detalle, tope=None):
    # Convierte filas en barras con ancho % relativo al máximo (o a un tope fijo, ej. 100).
    maximo = tope or max((valor(f) for f in filas), default=0)
    return [{
        "etiqueta": etiqueta(f),
        "valor": numero(valor(f)),
        "detalle": detalle(f),
        "ancho": min(100, round(valor(f) * 100 / maximo)) if maximo else 0,
        "destacada": maximo > 0 and valor(f) == maximo,
    } for f in filas]


def tarjeta_ocupacion(d):
    return {"valor": numero(d["porcentaje_ocupacion"], 1) + " %",
            "detalle": f"{numero(d['entradas_vendidas'])} de {numero(d['capacidad_total'])} butacas"}


def tarjeta_entradas(d):
    return {"valor": numero(d["entradas_vendidas"]), "detalle": "Entradas vendidas"}


def tarjeta_importe(d):
    return {"valor": pesos(d["monto_total"]),
            "detalle": f"Entradas {pesos(d['monto_entradas'])} · Servicios {pesos(d['monto_servicios'])}"}


def tarjeta_cancelaciones(d):
    return {"valor": numero(d["reservas_canceladas"]),
            "detalle": f"{numero(d['porcentaje_cancelacion'], 1)} % de {numero(d['reservas_totales'])} reservas"}
