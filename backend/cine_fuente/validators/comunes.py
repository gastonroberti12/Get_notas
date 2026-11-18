from cine_fuente.utils import construir_error_api


def error_validacion(titulo, detalle, codigo="ERROR_VALIDACION", status=400):
    """Corta la validación lanzando un ValueError con el formato de error de la API."""
    raise ValueError(construir_error_api(codigo, titulo, detalle), status)


def _ordenar(campos, referencia):
    """Respeta el orden de `referencia` si es lista/tupla; si no, ordena alfabéticamente."""
    if isinstance(referencia, (list, tuple)):
        return [campo for campo in referencia if campo in campos]
    return sorted(campos)


def validar_campos(
    body,
    permitidos=None,
    obligatorios=(),
    error_cuerpo=("Cuerpo JSON inválido", "El cuerpo debe ser un objeto JSON."),
    error_desconocidos=("Campos desconocidos", "No se admiten estos campos: {campos}."),
    error_faltantes=("Faltan campos obligatorios", "Se requieren: {campos}."),
):
    """Exige un objeto JSON, rechaza campos desconocidos y avisa los faltantes.

    - `permitidos=None` no controla campos desconocidos.
    - Los mensajes pueden usar `{campos}`, que se reemplaza por la lista separada por comas.
    - Devuelve el mismo `body` si es válido.
    """
    if not isinstance(body, dict):
        error_validacion(*error_cuerpo)

    if permitidos is not None:
        desconocidos = set(body) - set(permitidos)
        if desconocidos:
            titulo, detalle = error_desconocidos
            error_validacion(titulo, detalle.format(campos=", ".join(sorted(desconocidos))))

    faltantes = set(obligatorios) - set(body)
    if faltantes:
        titulo, detalle = error_faltantes
        error_validacion(titulo, detalle.format(campos=", ".join(_ordenar(faltantes, obligatorios))))

    return body


def validar_texto(valor, campo, maximo):
    """Texto no vacío, sin espacios laterales y de hasta `maximo` caracteres."""
    if not isinstance(valor, str) or not valor.strip():
        error_validacion("Campo inválido", f"'{campo}' debe ser un texto no vacío.")

    valor = valor.strip()

    if len(valor) > maximo:
        error_validacion("Campo inválido", f"'{campo}' no puede superar {maximo} caracteres.")

    return valor
