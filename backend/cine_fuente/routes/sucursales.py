from flask import Blueprint, jsonify, request
import pymysql
from cine_fuente.services.seguridad import requiere_rol
from cine_fuente.repositories.sucursales import actualizar_sucursal, consultar_sucursal_por_id, consultar_sucursales, eliminar_sucursal, insertar_sucursal
from cine_fuente.utils import (
    respuesta_error as error,
    respuesta_paginada,
    validar_paginacion,
)
from cine_fuente.validators.comunes import validar_texto

sucursales_bp = Blueprint("sucursales", __name__, url_prefix="/sucursales")


@sucursales_bp.route("", methods=["GET"])
# Lista las sucursales disponibles.
def listar_sucursales():
    limit, offset = validar_paginacion(request.args)
    sucursales = consultar_sucursales()
    return respuesta_paginada("sucursales", sucursales[offset:offset + limit], len(sucursales), limit, offset)


@sucursales_bp.route("/<int:sucursal_id>", methods=["GET"])
# Obtiene una sucursal por su identificador.
def obtener_sucursal(sucursal_id):
    sucursal = consultar_sucursal_por_id(sucursal_id)
    if sucursal is None:
        return error("sucursal.not.found", "Sucursal no encontrada", "La sucursal solicitada no existe.", 404)
    return jsonify(sucursal), 200


@sucursales_bp.route("", methods=["POST"])
@requiere_rol("administrador")
# Registra una nueva sucursal.
def crear_sucursal():
    datos = request.get_json(silent=True) or {}
    nombre = validar_texto(datos.get("nombre"), "nombre", 100)
    direccion = validar_texto(datos.get("direccion"), "direccion", 200)
    telefono = datos.get("telefono")
    if telefono is not None:
        telefono = str(telefono).strip() or None
    sucursal_id = insertar_sucursal(nombre, direccion, telefono)
    return jsonify(consultar_sucursal_por_id(sucursal_id)), 201


@sucursales_bp.route("/<int:sucursal_id>", methods=["PATCH"])
@requiere_rol("administrador")
# Actualiza los datos de una sucursal.
def modificar_sucursal(sucursal_id):
    if consultar_sucursal_por_id(sucursal_id) is None:
        return error("sucursal.not.found", "Sucursal no encontrada", "La sucursal solicitada no existe.", 404)
    datos = request.get_json(silent=True) or {}
    cambios = {}
    for campo, maximo in (("nombre", 100), ("direccion", 200)):
        if campo in datos:
            cambios[campo] = validar_texto(datos[campo], campo, maximo)
    if "telefono" in datos:
        cambios["telefono"] = str(datos["telefono"]).strip() or None
    if not cambios:
        return error("invalid.body", "Datos inválidos", "No se enviaron campos para modificar.", 400)
    actualizar_sucursal(sucursal_id, cambios)
    return "", 204


@sucursales_bp.route("/<int:sucursal_id>", methods=["DELETE"])
@requiere_rol("administrador")
# Elimina una sucursal existente.
def borrar_sucursal(sucursal_id):
    if consultar_sucursal_por_id(sucursal_id) is None:
        return error("sucursal.not.found", "Sucursal no encontrada", "La sucursal solicitada no existe.", 404)
    try:
        eliminar_sucursal(sucursal_id)
    except (pymysql.err.IntegrityError, Exception):
        return error("sucursal.has.relaciones", "No se puede eliminar", "La sucursal tiene salas relacionadas.", 409)
    return "", 204
