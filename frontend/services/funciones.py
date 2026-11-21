from services.api_cliente import LIMITE_LISTADOS, llamar_api

# pedidos al backend sobre las funciones


def listar_funciones(filtros=""):
    return llamar_api("GET", f"/funciones?_limit={LIMITE_LISTADOS}{filtros}")


def obtener_funcion(funcion_id):
    return llamar_api("GET", f"/funciones/{funcion_id}")


def obtener_butacas_disponibles(funcion_id):
    return llamar_api("GET", f"/funciones/{funcion_id}/butacas")


def crear_funcion(datos):
    return llamar_api("POST", "/funciones", datos)


def actualizar_funcion(funcion_id, datos):
    return llamar_api("PATCH", f"/funciones/{funcion_id}", datos)


def cambiar_estado_funcion(funcion_id, activa):
    return llamar_api("PATCH", f"/funciones/{funcion_id}", {"activa": activa})