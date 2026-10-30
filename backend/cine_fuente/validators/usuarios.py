from cine_fuente.validators.auth import validar_contrasenia, validar_email
from cine_fuente.validators.reservas import error_validacion, validar_entero_positivo

ROLES_VALIDOS = ("cliente", "administrador")
# Longitudes máximas según las columnas de la tabla usuarios.
LONGITUDES_MAXIMAS = {"nombre": 80, "email": 150}
CAMPOS_REGISTRO = ("nombre", "apellido", "email", "contrasenia")
CAMPOS_EDITABLES = ("nombre", "apellido", "email", "contrasenia", "rol")


def _validar_texto_busqueda(args, campo):
    """Devuelve el texto sin espacios laterales, o None si el parámetro no se envió."""
    valor = args.get(campo)
    if valor is None:
        return None
    valor = valor.strip()
    if not valor:
        error_validacion("Parámetro inválido", f"'{campo}' no puede estar vacío.")
    maximo = LONGITUDES_MAXIMAS[campo]
    if len(valor) > maximo:
        error_validacion("Parámetro inválido", f"'{campo}' no puede superar {maximo} caracteres.")
    return valor


def validar_filtros_usuarios(args) -> dict:
    """Valida los filtros admitidos por GET /usuarios: rol, nombre y email."""
    rol = args.get("rol")
    if rol is not None and rol not in ROLES_VALIDOS:
        error_validacion("Rol inválido", f"'rol' debe ser uno de: {', '.join(ROLES_VALIDOS)}.")

    return {
        "rol": rol,
        "nombre": _validar_texto_busqueda(args, "nombre"),
        "email": _validar_texto_busqueda(args, "email"),
    }


def validar_filtros_usuarios(args) -> dict:
    """Valida los filtros admitidos por GET /usuarios: rol, nombre y email."""
    rol = args.get("rol")
    if rol is not None and rol not in ROLES_VALIDOS:
        error_validacion("Rol inválido", f"'rol' debe ser uno de: {', '.join(ROLES_VALIDOS)}.")

    return {
        "rol": rol,
        "nombre": _validar_texto_busqueda(args, "nombre"),
        "email": _validar_texto_busqueda(args, "email"),
    }


def _validar_texto_obligatorio(valor, campo):
    """Texto no vacío, sin espacios laterales y dentro del largo de su columna."""
    if not isinstance(valor, str) or not valor.strip():
        error_validacion("Campo inválido", f"'{campo}' debe ser un texto no vacío.")
    valor = valor.strip()
    maximo = LONGITUDES_MAXIMAS[campo]
    if len(valor) > maximo:
        error_validacion("Campo inválido", f"'{campo}' no puede superar {maximo} caracteres.")
    return valor


def _validar_campo(campo, valor):
    """Aplica la validación propia de cada campo de usuario."""
    if campo == "email":
        return validar_email(valor)
    if campo == "contrasenia":
        return validar_contrasenia(valor)
    if campo == "rol":
        if valor not in ROLES_VALIDOS:
            error_validacion("Rol inválido", f"'rol' debe ser uno de: {', '.join(ROLES_VALIDOS)}.")
        return valor
    return _validar_texto_obligatorio(valor, campo)



def validar_body_crear_usuario(body) -> dict:
    """Valida el JSON de POST /usuarios: los cuatro campos son obligatorios y de tipo texto."""
    if not isinstance(body, dict):
        error_validacion("Cuerpo JSON inválido", "El cuerpo debe ser un objeto JSON.")

    faltantes = [campo for campo in CAMPOS_REGISTRO if campo not in body]
    if faltantes:
        error_validacion("Faltan campos obligatorios", f"Se requieren: {', '.join(faltantes)}.")

    datos = {}
    for campo in CAMPOS_REGISTRO:
        valor = body[campo]
        datos[campo] = _validar_campo(campo, valor)
    return datos


def validar_body_actualizar_usuario(body) -> dict:
    """Valida el JSON de PATCH /usuarios/{id}. Devuelve solo los campos enviados."""
    if not isinstance(body, dict) or not body:
        error_validacion("Cuerpo JSON inválido", "Envíe un objeto JSON con al menos un campo a modificar.")

    desconocidos = set(body) - set(CAMPOS_EDITABLES)
    if desconocidos:
        error_validacion("Campos desconocidos", f"No se admiten estos campos: {', '.join(sorted(desconocidos))}.")

    return {campo: _validar_campo(campo, valor) for campo, valor in body.items()}


def validar_id_usuario(id_usuario) -> int:
    """Valida el ID de la URL para GET/PATCH /usuarios/{id}."""
    return validar_entero_positivo(id_usuario, "id")