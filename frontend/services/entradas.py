from services.api_cliente import llamar_api

def validar_entrada(codigo_qr):
    return llamar_api("POST", "/entradas/validacion", {"codigo_qr": codigo_qr})