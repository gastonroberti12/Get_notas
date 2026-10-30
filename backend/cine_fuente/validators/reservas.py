from datetime import datetime
import re

from cine_fuente.utils import construir_error_api, ahora_gmt3


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


def validar_body_pago(body) -> None:
    """Valida los datos de tarjeta para el pago simulado sin almacenarlos."""
    # Se exige un objeto JSON con exactamente los cinco campos definidos.
    if not isinstance(body, dict):
        error_validacion("Cuerpo JSON inválido", "El cuerpo debe ser un objeto JSON.")
    campos = {"titular", "numero_tarjeta", "mes_vencimiento", "anio_vencimiento", "cvv"}

    desconocidos = set(body) - campos
    faltantes = campos - set(body)

    if desconocidos:
        error_validacion("Campos desconocidos", f"No se admiten estos campos: {', '.join(sorted(desconocidos))}.")
    if faltantes:
        error_validacion("Faltan campos obligatorios", f"Se requieren: {', '.join(sorted(faltantes))}.")

    # El titular admite letras, acentos y espacios.
    titular = body["titular"]

    if not isinstance(titular, str) or not re.fullmatch(
    r"[^\W\d_]+(?: [^\W\d_]+)+",
    titular.strip(),
    flags=re.UNICODE
    ):
        error_validacion(
            "Titular inválido",
            "'titular' debe contener nombre y apellido, utilizando solamente letras y espacios."
    )

    # El número debe ser texto de 13 a 19 dígitos ASCII y superar el control Luhn.
    numero = body["numero_tarjeta"]

    if not isinstance(numero, str) or not numero.isascii() or not numero.isdigit() or not 13 <= len(numero) <= 19:
        error_validacion(
            "Número de tarjeta inválido",
            "'numero_tarjeta' debe contener entre 13 y 19 dígitos, sin espacios ni guiones."
        )

    if not validar_luhn(numero):
        error_validacion(
            "Número de tarjeta inválido",
            "El número de tarjeta no supera la comprobación de dígito verificador."
        )

    # Se valida mes y año como cadenas para mantener el formato y los ceros iniciales.
    mes = body["mes_vencimiento"]
    anio = body["anio_vencimiento"]

    if not isinstance(mes, str) or not re.fullmatch(r"(?:0[1-9]|1[0-2])", mes):
        error_validacion("Vencimiento inválido", "'mes_vencimiento' debe ser un texto entre '01' y '12'.")

    if not isinstance(anio, str) or not anio.isascii() or not re.fullmatch(r"\d{4}", anio):
        error_validacion("Vencimiento inválido", "'anio_vencimiento' debe contener cuatro dígitos.")

    # Una tarjeta es válida hasta el último día de su mes de vencimiento.
    ahora = ahora_gmt3()

    if (int(anio), int(mes)) < (ahora.year, ahora.month):
        error_validacion(
            "Tarjeta vencida",
            "La tarjeta debe estar vigente al momento de realizar el pago."
        )

    # El CVV se trata como texto porque puede comenzar con cero.
    cvv = body["cvv"]

    if not isinstance(cvv, str) or not cvv.isascii() or not cvv.isdigit() or len(cvv) not in (3, 4):
        error_validacion(
            "Código de seguridad inválido",
            "'cvv' debe contener 3 o 4 dígitos."
        )

    # No se persisten los datos de tarjeta ni se devuelven en la respuesta.
    return None