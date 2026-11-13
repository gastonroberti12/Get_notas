from cine_fuente.utils import construir_error_api

CAMPOS_PERMITIDOS = {"calificacion", "comentario"}
COMENTARIO_MAXIMO = 500


def error_validacion(titulo, detalle):
    raise ValueError(construir_error_api("ERROR_VALIDACION", titulo, detalle), 400)


def validar_body_resena(datos):
    """Valida el JSON de una reseña y devuelve (calificacion, comentario)."""
    if not isinstance(datos, dict):
        error_validacion("Cuerpo inválido", "Se debe enviar un objeto JSON.")

    sobrantes = set(datos) - CAMPOS_PERMITIDOS
    if sobrantes:
        error_validacion("Cuerpo inválido", f"Campos no permitidos: {', '.join(sorted(sobrantes))}.")

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