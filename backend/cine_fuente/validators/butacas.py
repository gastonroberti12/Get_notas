from cine_fuente.validators.comunes import error_validacion, validar_campos


CAMPOS_BUTACA = {"sala_id", "fila", "numero"}
CAMPOS_MODIFICABLES = {"fila", "numero"}


def _entero(valor, campo):
    if type(valor) is int:
        return valor
    if isinstance(valor, str):
        try:
            return int(valor)
        except ValueError:
            pass
    error_validacion(
        "Datos inválidos",
        f"{campo} debe ser un entero.",
        "invalid.body",
    )


def _fila(valor):
    if not isinstance(valor, str):
        error_validacion(
            "Fila inválida",
            "fila debe ser una letra.",
            "invalid.fila.format",
        )
    fila = valor.strip().upper()
    if len(fila) != 1 or not fila.isalpha():
        error_validacion(
            "Fila inválida",
            "fila debe ser una letra.",
            "invalid.fila.format",
        )
    return fila


def validar_creacion_butaca(datos):
    validar_campos(
        datos,
        CAMPOS_BUTACA,
        obligatorios=("sala_id", "fila", "numero"),
        error_cuerpo=("Datos inválidos", "Se debe enviar un objeto JSON."),
        error_desconocidos=("Datos inválidos", "Campo(s) no permitido(s): {campos}."),
        error_faltantes=("Datos incompletos", "Falta(n) el/los campo(s): {campos}."),
    )

    sala_id = _entero(datos["sala_id"], "sala_id")
    fila = _fila(datos["fila"])
    numero = _entero(datos["numero"], "numero")
    if numero < 1:
        error_validacion(
            "Número inválido",
            "numero debe ser mayor que cero.",
            "invalid.numero.value",
        )
    return sala_id, fila, numero


def validar_modificacion_butaca(datos):
    validar_campos(
        datos,
        CAMPOS_MODIFICABLES,
        error_cuerpo=("Datos inválidos", "Se debe enviar un objeto JSON."),
        error_desconocidos=("Datos inválidos", "Campo(s) no permitido(s): {campos}."),
    )
    if not datos:
        error_validacion(
            "Datos inválidos",
            "No se enviaron campos para modificar.",
            "invalid.body",
        )

    cambios = {}
    if "fila" in datos:
        cambios["fila"] = _fila(datos["fila"])
    if "numero" in datos:
        numero = _entero(datos["numero"], "numero")
        if numero < 1:
            error_validacion(
                "Número inválido",
                "numero debe ser mayor que cero.",
                "invalid.numero.value",
            )
        cambios["numero"] = numero
    return cambios
