from urllib.parse import urlencode
from services.api_cliente import llamar_api

#pido al backend las estadísticas del backoffice.

BASE = "/admin/estadisticas"
RUTAS = {
    "general": "/ocupacion/general",
    "salas": "/ocupacion/salas",
    "franjas": "/ocupacion/franjas_horarias",
    "ventas": "/ventas/total",
    "generos": "/ventas/generos",
    "cancelaciones": "/cancelaciones",
}


def obtener_estadistica(clave, filtros): #arma la url de una estadistica y se la pide al back
    # filtros: {"fecha_desde": ..., "fecha_hasta": ...}; solo se mandan los que tienen valor.
    query = urlencode({k: v for k, v in filtros.items() if v}) #recorre el diccionario y solo copia los pares cuyo valor no es vacio
    sufijo = f"?{query}" if query else ""
    return llamar_api("GET", BASE + RUTAS[clave] + sufijo) #arma la ruta completa y la pide