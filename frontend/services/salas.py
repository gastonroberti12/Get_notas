from services.api_cliente import LIMITE_LISTADOS, llamar_api

def listar_salas():
    return llamar_api("GET", f"/salas?_limit={LIMITE_LISTADOS}")


def listar_butacas(sala_id):
    return llamar_api("GET", f"/salas/{sala_id}/butacas?_limit={LIMITE_LISTADOS}")