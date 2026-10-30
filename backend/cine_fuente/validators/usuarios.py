from cine_fuente.validators.reservas import error_validacion

ROLES_VALIDOS = ("cliente", "administrador")
# Longitudes máximas según las columnas de la tabla usuarios.
LONGITUDES_MAXIMAS = {"nombre": 80, "email": 150}
CAMPOS_REGISTRO = ("nombre", "apellido", "email", "contrasenia")


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
        if not isinstance(valor, str) or not valor.strip():
            error_validacion("Campo inválido", f"'{campo}' debe ser un texto no vacío.")
        datos[campo] = valor.strip()
    return datos