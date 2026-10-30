from flask import Blueprint, jsonify, request
from werkzeug.exceptions import HTTPException

from cine_fuente.services import funciones as service
from cine_fuente.validators import funciones as validator
from cine_fuente.utils import construir_error_api, respuesta_paginada, validar_paginacion

funciones_bp = Blueprint('funciones', __name__, url_prefix='/api/funciones')


@funciones_bp.get('')
def listar_funciones():
    limit, offset = validar_paginacion(request.args)
    filtros = validator.validar_filtros(request.args)
    funciones, total = service.obtener_funciones(filtros, limit, offset)
    return respuesta_paginada('funciones', funciones, total, limit, offset)


# Obtiene una función por su identificador.
@funciones_bp.get('/<int:funcion_id>')
def obtener_funcion(funcion_id):
    return jsonify(service.obtener_funcion_por_id(funcion_id)), 200


@funciones_bp.post('')
def crear_funcion():
    pelicula_id, sala_id, fecha_hora, precio = validator.validar_creacion(request.get_json(silent=True))
    return jsonify(service.crear_funcion(pelicula_id, sala_id, fecha_hora, precio)), 201


# Valida y aplica cambios a una función existente.
@funciones_bp.patch('/<int:funcion_id>')
def modificar_funcion(funcion_id):
    cambios = validator.validar_modificacion(request.get_json(silent=True) or {})
    service.actualizar_funcion_por_id(funcion_id, cambios)
    return '', 204


@funciones_bp.delete('/<int:funcion_id>')
def borrar_funcion(funcion_id):
    datos = request.get_json(silent=True) or {}
    service.eliminar_funcion_por_id(funcion_id, datos.get('fisica') is True)
    return '', 204


# Convierte errores de validación y negocio en respuestas HTTP.
@funciones_bp.errorhandler(ValueError)
def manejar_error_datos(error):
    respuesta = error.args[0]
    codigo = respuesta['errors'][0]['code']
    estados = {
        'funcion.not.found': 404,
        'pelicula.not.found': 404,
        'sala.not.found': 404,
        'funcion.overlap': 409,
        'funcion.has.reservas': 409,
    }
    return jsonify(respuesta), estados.get(codigo, 400)


@funciones_bp.errorhandler(HTTPException)
def manejar_http(error):
    raise error