from flask import Blueprint, jsonify, request
from werkzeug.exceptions import HTTPException

from cine_fuente.services import funciones as service
from cine_fuente.repositories.butacas import consultar_butacas_por_sala
from cine_fuente.repositories.reservas import obtener_butacas_ocupadas
from cine_fuente.validators import funciones as validator
from cine_fuente.utils import (
    construir_error_api,
    requiere_token,
    respuesta_error_api,
    respuesta_error_excepcion,
    respuesta_paginada,
    validar_paginacion,
)

funciones_bp = Blueprint('funciones', __name__, url_prefix='/api/funciones')


@funciones_bp.get('')
# Lista las funciones disponibles.
def listar_funciones():
    limit, offset = validar_paginacion(request.args)
    filtros = validator.validar_filtros(request.args)
    funciones, total = service.obtener_funciones(filtros, limit, offset)
    return respuesta_paginada('funciones', funciones, total, limit, offset)


# Obtiene una función por su identificador.
@funciones_bp.get('/<int:funcion_id>')
def obtener_funcion(funcion_id):
    return jsonify(service.obtener_funcion_por_id(funcion_id)), 200


@funciones_bp.get('/<int:funcion_id>/butacas')
# Consulta las butacas disponibles para una función.
def obtener_butacas_disponibles(funcion_id):
    funcion = service.obtener_funcion_por_id(funcion_id)
    if funcion is None:
        raise ValueError(construir_error_api(
            'funcion.not.found', 'Función no encontrada',
            'La función solicitada no existe.',
        ))
    butacas = consultar_butacas_por_sala(funcion['sala_id'])
    ocupadas = set(obtener_butacas_ocupadas(
        funcion_id,
        [butaca['id'] for butaca in butacas],
    ))
    disponibles = [
        butaca for butaca in butacas
        if butaca['id'] not in ocupadas
    ]
    return jsonify(disponibles), 200


@funciones_bp.post('')
@requiere_token(("administrador",))
# Registra una nueva función.
def crear_funcion():
    pelicula_id, sala_id, fecha_hora, precio = validator.validar_creacion(request.get_json(silent=True))
    return jsonify(service.crear_funcion(pelicula_id, sala_id, fecha_hora, precio)), 201


# Valida y aplica cambios a una función existente.
@funciones_bp.patch('/<int:funcion_id>')
@requiere_token(("administrador",))
def modificar_funcion(funcion_id):
    cambios = validator.validar_modificacion(request.get_json(silent=True) or {})
    service.actualizar_funcion_por_id(funcion_id, cambios)
    return '', 204


@funciones_bp.delete('/<int:funcion_id>')
@requiere_token(("administrador",))
# Elimina o desactiva una función.
def borrar_funcion(funcion_id):
    datos = request.get_json(silent=True) or {}
    service.eliminar_funcion_por_id(funcion_id, datos.get('fisica') is True)
    return '', 204


# Convierte errores de validación y negocio en respuestas HTTP.
@funciones_bp.errorhandler(ValueError)
def manejar_error_datos(error):
    respuesta = error.args[0]
    codigo = respuesta['errors'][0]['codigo']
    estados = {
        'funcion.not.found': 404,
        'pelicula.not.found': 404,
        'sala.not.found': 404,
        'funcion.overlap': 409,
        'funcion.has.reservas': 409,
    }
    if len(error.args) > 1 and isinstance(error.args[1], int):
        return respuesta_error_excepcion(error)
    return respuesta_error_api(respuesta, estados.get(codigo, 400))


@funciones_bp.errorhandler(HTTPException)
# Mantiene el manejo estándar de errores HTTP.
def manejar_http(error):
    raise error
