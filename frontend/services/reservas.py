from services.api_cliente import LIMITE_LISTADOS, llamar_api

def crear_reserva(funcion_id, butaca_ids):
    return llamar_api("POST", "/reservas", {"funcion_id": funcion_id, "butaca_ids": butaca_ids})


def obtener_reserva(reserva_id):
    return llamar_api("GET", f"/reservas/{reserva_id}")


def listar_entradas(reserva_id):
    return llamar_api("GET", f"/reservas/{reserva_id}/entradas?_limit={LIMITE_LISTADOS}")


def agregar_servicio(reserva_id, servicio_id, cantidad):
    datos = {"servicio_id": servicio_id, "cantidad": cantidad}
    return llamar_api("POST", f"/reservas/{reserva_id}/servicios", datos)


def pagar_reserva(reserva_id, datos_pago):
    return llamar_api("POST", f"/reservas/{reserva_id}/pago", datos_pago)


def cancelar_reserva(reserva_id):
    return llamar_api("PATCH", f"/reservas/{reserva_id}", {"estado": "cancelada"})