from datetime import timedelta

from cine_fuente.repositories import entradas as entradas_repo
from cine_fuente.services.reservas import entrada_api, normalizar_fecha_local
from cine_fuente.utils import ahora_gmt3, construir_error_api, formatear_fecha_hora
from constants import TOLERANCIA_INGRESO_MIN


def error_entrada(codigo, mensaje, estado):
    raise ValueError(construir_error_api(codigo, mensaje, mensaje), estado)


def listar_entradas(filtros, limit, offset):
    entradas = entradas_repo.listar_entradas(filtros, limit, offset)
    total = entradas_repo.contar_entradas(filtros)
    return [entrada_api(entrada) for entrada in entradas], total

def buscar_entrada(entrada_id):
    entrada = entradas_repo.obtener_entrada_por_id(entrada_id)
    if entrada is None:
        error_entrada("ENTRADA_NO_ENCONTRADA", "Entrada no encontrada", 404)
    return entrada


def obtener_entrada(entrada_id, usuario):
    entrada = buscar_entrada(entrada_id)
    es_dueno = int(entrada["usuario_id"]) == int(usuario["id"])
    if usuario["rol"] != "administrador" and not es_dueno:
        error_entrada("ACCESO_DENEGADO", "La entrada no pertenece al usuario", 403)
    return entrada_api(entrada)


def validar_entrada(entrada_id, codigo_qr):
    """Comprueba el ingreso y marca la entrada como utilizada una sola vez."""
    entrada = buscar_entrada(entrada_id)

    if entrada["estado_reserva"] != "confirmada":
        error_entrada("RESERVA_NO_CONFIRMADA", "La reserva no está confirmada", 409)

    if entrada["codigo_qr"] != codigo_qr:
        error_entrada("QR_INCORRECTO", "El código QR no corresponde a esta entrada", 400)

    if entrada["fecha_uso"] is not None:
        error_entrada("ENTRADA_YA_UTILIZADA", "La entrada ya fue utilizada", 409)

    duracion = entrada["duracion_min"]
    if duracion is None or duracion <= 0:
        error_entrada(
            "DURACION_NO_DISPONIBLE", "La película no tiene una duración válida", 409
        )

    ahora = ahora_gmt3()
    inicio = normalizar_fecha_local(entrada["fecha_hora"])
    fin = inicio + timedelta(minutes=int(duracion))
    if ahora < inicio - timedelta(minutes=TOLERANCIA_INGRESO_MIN) or ahora >= fin:
        error_entrada("FUNCION_FUERA_DE_HORARIO", "La entrada aún no está habilitada o la función ya terminó", 409)

    # MySQL guarda DATETIME sin zona horaria; mantenemos la hora local GMT-3.
    fecha_uso = ahora.replace(tzinfo=None)
    registrada = entradas_repo.registrar_uso_entrada(entrada_id, codigo_qr, fecha_uso, TOLERANCIA_INGRESO_MIN)
    if not registrada:
        error_entrada(
            "ENTRADA_NO_VALIDABLE",
            "La entrada ya fue utilizada o dejó de admitir el ingreso",
            409
        )

    entrada["fecha_uso"] = fecha_uso
    resultado = entrada_api(entrada)
    resultado["detalle"] = {
        "pelicula": entrada["pelicula_titulo"],
        "funcion": formatear_fecha_hora(entrada["fecha_hora"]),
        "sala": entrada["sala_nombre"],
        "butaca": f"{entrada['fila']}{entrada['numero']}",
    }
    return resultado   


def validar_por_qr(codigo_qr):
    entrada = entradas_repo.obtener_entrada_por_codigo_qr(codigo_qr)
    if entrada is None:
        entrada = entradas_repo.obtener_entrada_por_codigo_qr(codigo_qr.upper())
    if entrada is None:
        error_entrada("ENTRADA_NO_ENCONTRADA", "Entrada no encontrada", 404)
    return validar_entrada(entrada["id"], entrada["codigo_qr"])