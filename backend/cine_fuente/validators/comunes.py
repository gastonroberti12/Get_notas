from datetime import datetime

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


def validar_entero_positivo(valor, nombre: str) -> int:
    """Entero positivo: acepta int o texto con dígitos; rechaza booleanos."""
    if isinstance(valor, bool):
        error_validacion("Identificador inválido", f"'{nombre}' debe ser un entero positivo.")
    if isinstance(valor, int):
        entero = valor
    elif isinstance(valor, str) and valor.strip().isdecimal():
        entero = int(valor.strip())
    else:
        error_validacion("Identificador inválido", f"'{nombre}' debe ser un entero positivo.")
    if entero <= 0:
        error_validacion("Identificador inválido", f"'{nombre}' debe ser mayor que cero.")
    return entero


def validar_entero_json_positivo(valor, nombre: str) -> int:
    """Valida enteros JSON estrictos, rechazando strings y booleanos."""
    if not isinstance(valor, int) or isinstance(valor, bool) or valor <= 0:
        error_validacion("Identificador inválido", f"'{nombre}' debe ser un entero positivo en el JSON.")
    return valor


def validar_id_opcional(args, campo):
    """Devuelve el ID validado, o None si el parámetro no vino."""
    valor = args.get(campo)
    return None if valor is None else validar_entero_positivo(valor, campo)


def validar_rango_fechas(args, codigo_formato="fecha.invalid", codigo_rango="fecha.range.invalid"):
    """Valida fecha_desde/fecha_hasta (YYYY-MM-DD) y que desde <= hasta."""
    fechas = {}
    for campo in ("fecha_desde", "fecha_hasta"):
        texto = args.get(campo)
        if texto is None:
            fechas[campo] = None
            continue
        try:
            fecha = datetime.strptime(texto, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            fecha = None
        if fecha is None or fecha.isoformat() != texto:
            error_validacion("Fecha inválida", f"'{campo}' debe tener formato YYYY-MM-DD.", codigo_formato)
        fechas[campo] = fecha.isoformat()

    desde, hasta = fechas["fecha_desde"], fechas["fecha_hasta"]
    if desde is not None and hasta is not None and desde > hasta:
        error_validacion(
            "Rango de fechas inválido",
            "'fecha_desde' no puede ser posterior a 'fecha_hasta'.",
            codigo_rango,
        )
    return fechas


def validar_booleano_query(args, campo, codigo=None, titulo="Formato inválido", detalle=None):
    """Lee ?campo=true|false (sin importar mayúsculas). Devuelve None si no vino."""
    valor = args.get(campo)
    if valor is None:
        return None
    if valor.lower() not in ("true", "false"):
        error_validacion(
            titulo,
            detalle or f"{campo} debe ser true o false.",
            codigo or f"invalid.{campo}.format",
        )
    return valor.lower() == "true"
