from cine_fuente.validators.comunes import error_validacion, validar_campos

CAMPOS_PERMITIDOS = {"calificacion", "comentario"}
COMENTARIO_MAXIMO = 500


def validar_body_resena(datos):
    """Valida el JSON de una reseña y devuelve (calificacion, comentario)."""
    validar_campos(
        datos,
        CAMPOS_PERMITIDOS,
        error_cuerpo=("Cuerpo inválido", "Se debe enviar un objeto JSON."),
        error_desconocidos=("Cuerpo inválido", "Campos no permitidos: {campos}."),
    )

    calificacion = datos.get("calificacion")
    if not isinstance(calificacion, int) or isinstance(calificacion, bool) or not 1 <= calificacion <= 5:
        error_validacion("Calificación inválida", "calificacion debe ser un entero entre 1 y 5.")

    comentario = datos.get("comentario")
    if comentario is not None:
        if not isinstance(comentario, str):
            error_validacion("Comentario inválido", "comentario debe ser un texto.")
        comentario = comentario.strip()
        if len(comentario) > COMENTARIO_MAXIMO:
            error_validacion(
                "Comentario inválido",
                f"comentario no puede superar los {COMENTARIO_MAXIMO} caracteres.",
            )
        comentario = comentario or None

    return calificacion, comentario