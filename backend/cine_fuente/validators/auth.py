import re # Importa expresiones regulares para validar el formato del email

from cine_fuente.validators.comunes import error_validacion, validar_campos

CAMPOS_CREDENCIALES = {"email", "contrasenia"}
EMAIL_LONGITUD_MAXIMA = 150
CONTRASENIA_LONGITUD_MINIMA = 8
CONTRASENIA_LONGITUD_MAXIMA = 128
PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_email(email) -> str:
    """Valida formato y largo del email; lo devuelve sin espacios laterales."""
    if not isinstance(email, str) or not email.strip():
        error_validacion("Email inválido", "'email' debe ser un texto no vacío.")
    email = email.strip()
    if len(email) > EMAIL_LONGITUD_MAXIMA:
        error_validacion("Email inválido", f"'email' no puede superar {EMAIL_LONGITUD_MAXIMA} caracteres.")
    if not PATRON_EMAIL.match(email):
        error_validacion("Email inválido", "'email' debe tener un formato de correo electrónico válido.")
    return email


def validar_contrasenia(contrasenia) -> str:
    """Valida tipo y largo de la contraseña; no la modifica."""
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
    return contrasenia


def validar_body_login(body) -> dict:
    """Valida el JSON de login y devuelve {'email': ..., 'contrasenia': ...} arreglado.

    El email se devuelve sin espacios laterales; la contraseña no se modifica.
    Levanta ValueError (400) si falta algún campo o alguno es inválido.
    """
    validar_campos(body, CAMPOS_CREDENCIALES, CAMPOS_CREDENCIALES)
    return {
        "email": validar_email(body["email"]),
        "contrasenia": validar_contrasenia(body["contrasenia"]),
    }