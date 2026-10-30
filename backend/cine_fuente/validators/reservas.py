from datetime import datetime

from cine_fuente.utils import construir_error_api


def error_validacion(mensaje: str, detalle: str):
    raise ValueError(construir_error_api("ERROR_VALIDACION", mensaje, detalle), 400)


def validar_entero_positivo(valor, nombre: str) -> int:
    """Valida IDs usados"""
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


def validar_body_crear_reserva(body) -> dict:
    """Valida el JSON antes de consultar la base de datos."""
    if not isinstance(body, dict):
        error_validacion("Cuerpo JSON inválido", "El cuerpo debe ser un objeto JSON.")

    campos = {"funcion_id", "butaca_ids"}
    desconocidos = set(body) - campos
    faltantes = campos - set(body)
    if desconocidos:
        error_validacion("Campos desconocidos", f"No se admiten estos campos: {', '.join(sorted(desconocidos))}.")
    if faltantes:
        error_validacion("Faltan campos obligatorios", f"Se requieren: {', '.join(sorted(faltantes))}.")

    funcion_id = validar_entero_json_positivo(body["funcion_id"], "funcion_id")
    butaca_ids = body["butaca_ids"]
    if not isinstance(butaca_ids, list) or not butaca_ids:
        error_validacion("Butacas inválidas", "'butaca_ids' debe ser una lista no vacía de identificadores.")

    ids_validados = [validar_entero_json_positivo(valor, "butaca_ids") for valor in butaca_ids]
    if len(ids_validados) != len(set(ids_validados)):
        error_validacion("Butacas duplicadas", "No se puede enviar una butaca más de una vez.")

    return {"funcion_id": funcion_id, "butaca_ids": ids_validados}


def validar_body_cancelar_reserva(body) -> dict:
    """Valida el JSON, solo admite estado='cancelada'."""
    if not isinstance(body, dict):
        error_validacion("Cuerpo JSON inválido", "El cuerpo debe ser un objeto JSON.")
    if set(body) != {"estado"}:
        error_validacion("Cuerpo inválido", "El cuerpo debe contener únicamente el campo 'estado'.")
    if body.get("estado") != "cancelada":
        error_validacion("Estado inválido", "El único estado admitido en esta operación es 'cancelada'.")
    return {"estado": "cancelada"}


def validar_id_reserva(id_reserva) -> int:
    """Valida el ID empleado por GET, PATCH, pago y entradas de una reserva."""
    return validar_entero_positivo(id_reserva, "id")


def validar_filtros_listado(args) -> dict:
    """Valida filtros admitidos."""
    filtros = {}
    estados_validos = ("pendiente", "confirmada", "cancelada", "expirada", "finalizada")
    for campo in ("usuario_id", "funcion_id"):
        valor = args.get(campo)
        filtros[campo] = validar_entero_positivo(valor, campo) if valor is not None else None

    estado = args.get("estado")
    if estado is not None and estado not in estados_validos:
        error_validacion("Estado inválido", f"'estado' debe ser uno de: {', '.join(estados_validos)}.")
    filtros["estado"] = estado

    fechas = {}
    for campo in ("fecha_desde", "fecha_hasta"):
        texto = args.get(campo)
        if texto is None:
            fechas[campo] = None
            continue
        try:
            fecha = datetime.strptime(texto, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            error_validacion("Fecha inválida", f"'{campo}' debe tener formato YYYY-MM-DD.")
        if fecha.isoformat() != texto:
            error_validacion("Fecha inválida", f"'{campo}' debe tener formato YYYY-MM-DD.")
        fechas[campo] = fecha.isoformat()

    if fechas["fecha_desde"] and fechas["fecha_hasta"] and fechas["fecha_desde"] > fechas["fecha_hasta"]:
        error_validacion("Rango de fechas inválido", "'fecha_desde' no puede ser posterior a 'fecha_hasta'.")
    filtros.update(fechas)
    return filtros


def validar_estado_propio(args) -> str | None:
    """Valida el filtro estado de GET /usuarios/me/reservas."""
    estados_validos = ("pendiente", "confirmada", "cancelada", "expirada", "finalizada")
    estado = args.get("estado")
    if estado is not None and estado not in estados_validos:
        error_validacion("Estado inválido", f"'estado' debe ser uno de: {', '.join(estados_validos)}.")
    return estado


def validar_luhn(numero: str) -> bool:
    """Comprueba el dígito verificador; no demuestra que la tarjeta exista o tenga fondos."""
    suma = 0
    # La paridad determina qué dígitos se duplican al recorrer el número desde la derecha.
    paridad = len(numero) % 2
    for indice, caracter in enumerate(numero):
        digito = int(caracter)
        if indice % 2 == paridad:
            digito *= 2
            if digito > 9:
                digito -= 9
        suma += digito
    # Un número supera Luhn cuando la suma total es múltiplo de diez.
    return suma % 10 == 0