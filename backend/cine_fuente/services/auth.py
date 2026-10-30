from cine_fuente.repositories import usuarios as usuarios_repo
from cine_fuente.services.seguridad import generar_token, verificar_contrasenia
from cine_fuente.services.usuarios import usuario_api
from cine_fuente.utils import construir_error_api


def iniciar_sesion(credenciales: dict) -> dict:
    """Devuelve {'token', 'usuario'}; ante cualquier fallo, un 401 genérico (ValueError)."""
    fila = usuarios_repo.obtener_usuario_por_email(credenciales["email"])

    if fila is None or not verificar_contrasenia(fila["contrasena"], credenciales["contrasenia"]):
        raise ValueError(construir_error_api(
            "CREDENCIALES_INVALIDAS",
            "Credenciales inválidas",
            "El email o la contraseña son incorrectos.",
        ), 401)

    token = generar_token(int(fila["id"]), fila["rol"])
    return {"token": token, "usuario": usuario_api(fila)}