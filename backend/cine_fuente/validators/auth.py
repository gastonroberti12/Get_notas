import re # Importa expresiones regulares para validar el formato del email

from cine_fuente.validators.reservas import error_validacion

CAMPOS_CREDENCIALES = {"email", "contrasenia"}
EMAIL_LONGITUD_MAXIMA = 150
CONTRASENIA_LONGITUD_MINIMA = 8
CONTRASENIA_LONGITUD_MAXIMA = 128
PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_body_login(body) -> dict:
    """Valida el JSON de login y devuelve {'email': ..., 'contrasenia': ...} arreglado.

    El email se devuelve sin espacios laterales; la contraseña no se modifica.
    Levanta ValueError (400) si falta algún campo o alguno es inválido.
    """
    if not isinstance(body, dict):
        error_validacion("Cuerpo JSON inválido", "El cuerpo debe ser un objeto JSON.")

    desconocidos = set(body) - CAMPOS_CREDENCIALES
    faltantes = CAMPOS_CREDENCIALES - set(body)
    if desconocidos:
        error_validacion("Campos desconocidos", f"No se admiten estos campos: {', '.join(sorted(desconocidos))}.")
    if faltantes:
        error_validacion("Faltan campos obligatorios", f"Se requieren: {', '.join(sorted(faltantes))}.")

    email = body["email"]
    if not isinstance(email, str) or not email.strip():
        error_validacion("Email inválido", "'email' debe ser un texto no vacío.")
    email = email.strip()
    if len(email) > EMAIL_LONGITUD_MAXIMA:
        error_validacion("Email inválido", f"'email' no puede superar {EMAIL_LONGITUD_MAXIMA} caracteres.")
    if not PATRON_EMAIL.match(email):
        error_validacion("Email inválido", "'email' debe tener un formato de correo electrónico válido.")

    contrasenia = body["contrasenia"]
    if not isinstance(contrasenia, str):
        error_validacion("Contraseña inválida", "'contrasenia' debe ser un texto.")
    if len(contrasenia) < CONTRASENIA_LONGITUD_MINIMA:
        error_validacion(
            "Contraseña inválida",
            f"'contrasenia' debe tener al menos {CONTRASENIA_LONGITUD_MINIMA} caracteres.",
        )
    if len(contrasenia) > CONTRASENIA_LONGITUD_MAXIMA:
        error_validacion(
            "Contraseña inválida",
            f"'contrasenia' no puede superar {CONTRASENIA_LONGITUD_MAXIMA} caracteres.",
        )

    return {"email": email, "contrasenia": contrasenia}