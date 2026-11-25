from services.api_cliente import LIMITE_LISTADOS, llamar_api

def iniciar_sesion(email, contrasenia):
    return llamar_api("POST", "/auth/login", {"email": email, "contrasenia": contrasenia})


def cerrar_sesion():
    return llamar_api("POST", "/auth/logout")


def registrar_usuario(datos):
    return llamar_api("POST", "/usuarios", datos)


def obtener_mi_usuario():
    return llamar_api("GET", "/usuarios/me")


def actualizar_usuario(usuario_id, datos):
    return llamar_api("PATCH", f"/usuarios/{usuario_id}", datos)


def actualizar_contrasenia(actual, nueva):
    datos = {"contrasenia_actual": actual, "contrasenia_nueva": nueva}
    return llamar_api("POST", "/usuarios/me/contrasenia", datos)


def listar_mis_reservas(filtros=""):
    return llamar_api("GET", f"/usuarios/me/reservas?_limit={LIMITE_LISTADOS}{filtros}")


def listar_mis_resenas():
    return llamar_api("GET", f"/usuarios/me/resenas?_limit={LIMITE_LISTADOS}")