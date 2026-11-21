from services.api_cliente import LIMITE_LISTADOS, llamar_api

def listar_sucursales():
    return llamar_api("GET", f"/sucursales?_limit={LIMITE_LISTADOS}")