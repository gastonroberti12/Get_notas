from flask import Blueprint, jsonify, request
import pymysql

from cine_fuente.repositories.salas import actualizar_sala, consultar_sala_por_id, consultar_salas, eliminar_sala, insertar_sala
from cine_fuente.repositories.sucursales import consultar_sucursal_por_id
from cine_fuente.utils import construir_error_api, respuesta_paginada, validar_paginacion

salas_bp = Blueprint("salas", __name__, url_prefix="/api/salas")


def error(codigo, mensaje, descripcion, estado):
    return jsonify(construir_error_api(codigo, mensaje, descripcion)), estado


@salas_bp.get("")
# Lista las salas disponibles.
def listar_salas():
    try:
        limit, offset = validar_paginacion(request.args)
        salas = consultar_salas(request.args.get("sucursal_id", type=int))
    except ValueError as error_validacion:
        return jsonify(error_validacion.args[0]), 400
    return respuesta_paginada("salas", salas[offset:offset + limit], len(salas), limit, offset)


@salas_bp.get("/<int:sala_id>")
# Obtiene una sala por su identificador.
def obtener_sala(sala_id):
    sala = consultar_sala_por_id(sala_id)
    if sala is None:
        return error("sala.not.found", "Sala no encontrada", "La sala solicitada no existe.", 404)
    return jsonify(sala), 200


@salas_bp.post("")
# Registra una nueva sala.
def crear_sala():
    datos = request.get_json(silent=True) or {}
    try:
        sucursal_id = int(datos["sucursal_id"])
        nombre = str(datos["nombre"]).strip()
        capacidad = int(datos["capacidad"])
        if not nombre or len(nombre) > 50:
            raise ValueError(construir_error_api("invalid.nombre.value", "Nombre inválido", "nombre debe tener entre 1 y 50 caracteres."))
        if capacidad < 1:
            raise ValueError(construir_error_api("invalid.capacidad.value", "Capacidad inválida", "capacidad debe ser mayor que cero."))
    except KeyError as campo:
        return error("invalid.body", "Datos incompletos", f"Falta el campo '{campo.args[0]}'.", 400)
    except (TypeError, ValueError) as error_validacion:
        respuesta = error_validacion.args[0] if error_validacion.args else construir_error_api("invalid.body", "Datos inválidos", "Los datos enviados no son válidos.")
        return jsonify(respuesta), 400
    if consultar_sucursal_por_id(sucursal_id) is None:
        return error("sucursal.not.found", "Sucursal no encontrada", "La sucursal indicada no existe.", 404)
    try:
        sala_id = insertar_sala(sucursal_id, nombre, capacidad)
    except pymysql.err.IntegrityError:
        return error("sala.nombre.duplicado", "Sala duplicada", "Ya existe una sala con ese nombre en la sucursal.", 409)
    return jsonify(consultar_sala_por_id(sala_id)), 201


@salas_bp.patch("/<int:sala_id>")
# Actualiza los datos de una sala.
def modificar_sala(sala_id):
    if consultar_sala_por_id(sala_id) is None:
        return error("sala.not.found", "Sala no encontrada", "La sala solicitada no existe.", 404)
    datos = request.get_json(silent=True) or {}
    cambios = {}
    if "nombre" in datos:
        nombre = str(datos["nombre"]).strip()
        if not nombre or len(nombre) > 50:
            return error("invalid.nombre.value", "Nombre inválido", "nombre debe tener entre 1 y 50 caracteres.", 400)
        cambios["nombre"] = nombre
    if "capacidad" in datos:
        try:
            capacidad = int(datos["capacidad"])
            if capacidad < 1:
                raise ValueError
        except (TypeError, ValueError):
            return error("invalid.capacidad.value", "Capacidad inválida", "capacidad debe ser un entero mayor que cero.", 400)
        cambios["capacidad"] = capacidad
    if "sucursal_id" in datos:
        try:
            sucursal_id = int(datos["sucursal_id"])
        except (TypeError, ValueError):
            return error("invalid.sucursal_id.format", "Formato inválido", "sucursal_id debe ser un entero.", 400)
        if consultar_sucursal_por_id(sucursal_id) is None:
            return error("sucursal.not.found", "Sucursal no encontrada", "La sucursal indicada no existe.", 404)
        cambios["sucursal_id"] = sucursal_id
    if not cambios:
        return error("invalid.body", "Datos inválidos", "No se enviaron campos para modificar.", 400)
    try:
        actualizar_sala(sala_id, cambios)
    except pymysql.err.IntegrityError:
        return error("sala.nombre.duplicado", "Sala duplicada", "Ya existe una sala con ese nombre en la sucursal.", 409)
    return "", 204


@salas_bp.delete("/<int:sala_id>")
# Elimina una sala existente.
def borrar_sala(sala_id):
    if consultar_sala_por_id(sala_id) is None:
        return error("sala.not.found", "Sala no encontrada", "La sala solicitada no existe.", 404)
    try:
        eliminar_sala(sala_id)
    except Exception:
        return error("sala.has.relaciones", "No se puede eliminar", "La sala tiene funciones o butacas relacionadas.", 409)
    return "", 204
