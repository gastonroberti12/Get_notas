from flask import Blueprint, jsonify, request
import pymysql

from cine_fuente.repositories.butacas import consultar_butaca_por_id, consultar_butacas_por_sala, contar_butacas, eliminar_butaca, eliminar_butacas_de_sala, insertar_butaca
from cine_fuente.repositories.salas import consultar_sala_por_id
from cine_fuente.utils import construir_error_api, respuesta_paginada, validar_paginacion

butacas_bp = Blueprint("butacas", __name__, url_prefix="/api")


def error(codigo, mensaje, descripcion, estado):
    return jsonify(construir_error_api(codigo, mensaje, descripcion)), estado


@butacas_bp.get("/salas/<int:sala_id>/butacas")
# Lista las butacas de una sala.
def listar_butacas_sala(sala_id):
    if consultar_sala_por_id(sala_id) is None:
        return error("sala.not.found", "Sala no encontrada", "La sala solicitada no existe.", 404)
    try:
        limit, offset = validar_paginacion(request.args)
        butacas = consultar_butacas_por_sala(sala_id)
    except ValueError as error_validacion:
        return jsonify(error_validacion.args[0]), 400
    return respuesta_paginada("butacas", butacas[offset:offset + limit], len(butacas), limit, offset)


@butacas_bp.post("/salas/<int:sala_id>/butacas/generar")
# Genera las butacas de una sala.
def generar_butacas(sala_id):
    sala = consultar_sala_por_id(sala_id)
    if sala is None:
        return error("sala.not.found", "Sala no encontrada", "La sala solicitada no existe.", 404)
    capacidad = sala["capacidad"]
    if capacidad % 10 != 0:
        return error("sala.capacidad.invalid", "Capacidad inválida", "La capacidad debe ser múltiplo de 10 para generar butacas.", 400)
    if contar_butacas(sala_id) != 0:
        return error("butacas.already.generated", "Butacas ya generadas", "La sala ya tiene butacas generadas.", 409)
    cantidad = 0
    for fila_numero in range(1, capacidad // 10 + 1):
        fila = chr(64 + fila_numero)
        for numero in range(1, 11):
            insertar_butaca(sala_id, fila, numero)
            cantidad += 1
    return jsonify({"mensaje": "Butacas generadas", "cantidad": cantidad}), 201


@butacas_bp.post("/butacas")
# Registra una nueva butaca.
def crear_butaca():
    datos = request.get_json(silent=True) or {}
    try:
        sala_id = int(datos["sala_id"])
        fila = str(datos["fila"]).strip().upper()
        numero = int(datos["numero"])
        if not fila or len(fila) != 1 or not fila.isalpha():
            return error("invalid.fila.format", "Fila inválida", "fila debe ser una letra.", 400)
        if numero < 1:
            return error("invalid.numero.value", "Número inválido", "numero debe ser mayor que cero.", 400)
    except KeyError as campo:
        return error("invalid.body", "Datos incompletos", f"Falta el campo '{campo.args[0]}'.", 400)
    except (TypeError, ValueError):
        return error("invalid.body", "Datos inválidos", "sala_id y numero deben ser enteros.", 400)
    if consultar_sala_por_id(sala_id) is None:
        return error("sala.not.found", "Sala no encontrada", "La sala indicada no existe.", 404)
    try:
        butaca_id = insertar_butaca(sala_id, fila, numero)
    except pymysql.err.IntegrityError:
        return error("butaca.duplicada", "Butaca duplicada", "La fila y el número ya existen en la sala.", 409)
    return jsonify(consultar_butaca_por_id(butaca_id)), 201


@butacas_bp.delete("/butacas/<int:butaca_id>")
# Elimina una butaca.
def borrar_butaca(butaca_id):
    if consultar_butaca_por_id(butaca_id) is None:
        return error("butaca.not.found", "Butaca no encontrada", "La butaca solicitada no existe.", 404)
    try:
        eliminar_butaca(butaca_id)
    except Exception:
        return error("butaca.has.reservas", "No se puede eliminar", "La butaca tiene entradas relacionadas.", 409)
    return "", 204


@butacas_bp.delete("/salas/<int:sala_id>/butacas")
# Elimina las butacas de una sala.
def borrar_butacas_sala(sala_id):
    if consultar_sala_por_id(sala_id) is None:
        return error("sala.not.found", "Sala no encontrada", "La sala solicitada no existe.", 404)
    try:
        eliminar_butacas_de_sala(sala_id)
    except Exception:
        return error("butacas.has.reservas", "No se pueden eliminar", "Las butacas tienen entradas relacionadas.", 409)
    return "", 204
