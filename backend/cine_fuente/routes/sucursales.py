from flask import Blueprint, jsonify, request
import pymysql

from cine_fuente.repositories.sucursales import actualizar_sucursal, consultar_sucursal_por_id, consultar_sucursales, eliminar_sucursal, insertar_sucursal
from cine_fuente.utils import (
    construir_error_api,
    requiere_token,
    respuesta_error_api,
    respuesta_error_excepcion,
    respuesta_paginada,
    validar_paginacion,
)

sucursales_bp = Blueprint("sucursales", __name__, url_prefix="/api/sucursales")


def error(codigo, mensaje, descripcion, estado):
    return respuesta_error_api(construir_error_api(codigo, mensaje, descripcion), estado)


def validar_texto(datos, campo, maximo):
    valor = datos.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(construir_error_api(f"required.{campo}", f"Campo requerido: '{campo}'", f"El campo '{campo}' es obligatorio."))
    valor = valor.strip()
    if len(valor) > maximo:
        raise ValueError(construir_error_api(f"invalid.{campo}.max", "Valor demasiado largo", f"{campo} no puede superar {maximo} caracteres."))
    return valor


@sucursales_bp.get("")
# Lista las sucursales disponibles.
def listar_sucursales():
    try:
        limit, offset = validar_paginacion(request.args)
        sucursales = consultar_sucursales()
    except ValueError as error_validacion:
        return respuesta_error_excepcion(error_validacion)
    return respuesta_paginada("sucursales", sucursales[offset:offset + limit], len(sucursales), limit, offset)


@sucursales_bp.get("/<int:sucursal_id>")
# Obtiene una sucursal por su identificador.
def obtener_sucursal(sucursal_id):
    sucursal = consultar_sucursal_por_id(sucursal_id)
    if sucursal is None:
        return error("sucursal.not.found", "Sucursal no encontrada", "La sucursal solicitada no existe.", 404)
    return jsonify(sucursal), 200


@sucursales_bp.post("")
@requiere_token(("administrador",))
# Registra una nueva sucursal.
def crear_sucursal():
    datos = request.get_json(silent=True) or {}
    try:
        nombre = validar_texto(datos, "nombre", 100)
        direccion = validar_texto(datos, "direccion", 200)
        telefono = datos.get("telefono")
        if telefono is not None:
            telefono = str(telefono).strip() or None
    except ValueError as error_validacion:
        return respuesta_error_excepcion(error_validacion)
    sucursal_id = insertar_sucursal(nombre, direccion, telefono)
    return jsonify(consultar_sucursal_por_id(sucursal_id)), 201


@sucursales_bp.patch("/<int:sucursal_id>")
@requiere_token(("administrador",))
# Actualiza los datos de una sucursal.
def modificar_sucursal(sucursal_id):
    if consultar_sucursal_por_id(sucursal_id) is None:
        return error("sucursal.not.found", "Sucursal no encontrada", "La sucursal solicitada no existe.", 404)
    datos = request.get_json(silent=True) or {}
    cambios = {}
    try:
        for campo, maximo in (("nombre", 100), ("direccion", 200)):
            if campo in datos:
                cambios[campo] = validar_texto(datos, campo, maximo)
        if "telefono" in datos:
            cambios["telefono"] = str(datos["telefono"]).strip() or None
    except ValueError as error_validacion:
        return respuesta_error_excepcion(error_validacion)
    if not cambios:
        return error("invalid.body", "Datos inválidos", "No se enviaron campos para modificar.", 400)
    actualizar_sucursal(sucursal_id, cambios)
    return "", 204


@sucursales_bp.delete("/<int:sucursal_id>")
@requiere_token(("administrador",))
# Elimina una sucursal existente.
def borrar_sucursal(sucursal_id):
    if consultar_sucursal_por_id(sucursal_id) is None:
        return error("sucursal.not.found", "Sucursal no encontrada", "La sucursal solicitada no existe.", 404)
    try:
        eliminar_sucursal(sucursal_id)
    except (pymysql.err.IntegrityError, Exception):
        return error("sucursal.has.relaciones", "No se puede eliminar", "La sucursal tiene salas relacionadas.", 409)
    return "", 204
