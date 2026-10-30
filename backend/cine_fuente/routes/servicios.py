from flask import Blueprint, jsonify, request
import pymysql

from cine_fuente.repositories.servicios import (
    actualizar_servicio, consultar_servicio_por_id, consultar_servicios,
    desactivar_servicio, insertar_servicio,
)
from cine_fuente.utils import construir_error_api, respuesta_paginada, validar_paginacion

servicios_bp = Blueprint("servicios", __name__, url_prefix="/api/servicios")


def error(codigo, mensaje, descripcion, estado):
    return jsonify(construir_error_api(codigo, mensaje, descripcion)), estado


def validar_texto(valor, campo, maximo):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(construir_error_api(f"required.{campo}", f"Campo requerido: '{campo}'", f"El campo '{campo}' es obligatorio."))
    valor = valor.strip()
    if len(valor) > maximo:
        raise ValueError(construir_error_api(f"invalid.{campo}.max", "Valor demasiado largo", f"{campo} no puede superar {maximo} caracteres."))
    return valor


def validar_precio(valor):
    try:
        precio = float(valor)
    except (TypeError, ValueError):
        raise ValueError(construir_error_api("invalid.precio.format", "Formato inválido", "precio debe ser un número mayor que cero."))
    if precio <= 0:
        raise ValueError(construir_error_api("invalid.precio.value", "Precio inválido", "precio debe ser mayor que cero."))
    return precio


@servicios_bp.get("")
# Lista los servicios disponibles.
def listar_servicios():
    try:
        limit, offset = validar_paginacion(request.args)
        servicios = consultar_servicios()
    except ValueError as error_validacion:
        return jsonify(error_validacion.args[0]), 400
    return respuesta_paginada("servicios", servicios[offset:offset + limit], len(servicios), limit, offset)


@servicios_bp.get("/<int:servicio_id>")
# Obtiene un servicio por su identificador.
def obtener_servicio(servicio_id):
    servicio = consultar_servicio_por_id(servicio_id)
    if servicio is None:
        return error("servicio.not.found", "Servicio no encontrado", "El servicio solicitado no existe.", 404)
    return jsonify(servicio), 200


@servicios_bp.post("")
# Registra un nuevo servicio.
def crear_servicio():
    datos = request.get_json(silent=True) or {}
    try:
        nombre = validar_texto(datos.get("nombre"), "nombre", 100)
        descripcion = validar_texto(datos.get("descripcion"), "descripcion", 255) if datos.get("descripcion") else None
        precio = validar_precio(datos.get("precio"))
    except ValueError as error_validacion:
        return jsonify(error_validacion.args[0]), 400
    try:
        servicio_id = insertar_servicio(nombre, descripcion, precio)
    except pymysql.err.IntegrityError:
        return error("servicio.nombre.duplicado", "Servicio duplicado", "Ya existe un servicio con ese nombre.", 409)
    return jsonify(consultar_servicio_por_id(servicio_id)), 201


@servicios_bp.patch("/<int:servicio_id>")
# Actualiza los datos de un servicio.
def modificar_servicio(servicio_id):
    if consultar_servicio_por_id(servicio_id) is None:
        return error("servicio.not.found", "Servicio no encontrado", "El servicio solicitado no existe.", 404)
    datos = request.get_json(silent=True) or {}
    cambios = {}
    try:
        if "nombre" in datos:
            cambios["nombre"] = validar_texto(datos["nombre"], "nombre", 100)
        if "descripcion" in datos:
            cambios["descripcion"] = validar_texto(datos["descripcion"], "descripcion", 255) if datos["descripcion"] else None
        if "precio" in datos:
            cambios["precio"] = validar_precio(datos["precio"])
        if "activo" in datos:
            if not isinstance(datos["activo"], bool):
                return error("invalid.activo.format", "Formato inválido", "activo debe ser true o false.", 400)
            cambios["activo"] = datos["activo"]
    except ValueError as error_validacion:
        return jsonify(error_validacion.args[0]), 400
    if not cambios:
        return error("invalid.body", "Datos inválidos", "No se enviaron campos para modificar.", 400)
    actualizar_servicio(servicio_id, cambios)
    return "", 204


@servicios_bp.delete("/<int:servicio_id>")
# Desactiva un servicio.
def borrar_servicio(servicio_id):
    if consultar_servicio_por_id(servicio_id) is None:
        return error("servicio.not.found", "Servicio no encontrado", "El servicio solicitado no existe.", 404)
    desactivar_servicio(servicio_id)
    return "", 204
