from services.api_cliente import LIMITE_LISTADOS, llamar_api

def listar_servicios(filtros=""):
    return llamar_api("GET", f"/servicios?_limit={LIMITE_LISTADOS}{filtros}")


def obtener_servicio(servicio_id):
    return llamar_api("GET", f"/servicios/{servicio_id}")


def crear_servicio(datos):
    return llamar_api("POST", "/servicios", datos)


def actualizar_servicio(servicio_id, datos):
    return llamar_api("PATCH", f"/servicios/{servicio_id}", datos)


def actualizar_estado_servicio(servicio_id, activo):
    return llamar_api("PATCH", f"/servicios/{servicio_id}", {"activo": activo})