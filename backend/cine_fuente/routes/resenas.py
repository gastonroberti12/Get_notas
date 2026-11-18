from flask import Blueprint, g, jsonify, request

from cine_fuente.services.seguridad import requiere_rol
from cine_fuente.services import resenas as resenas_service
from cine_fuente.validators.resenas import validar_body_resena
from cine_fuente.utils import (
    validar_paginacion,
)

resenas_bp = Blueprint("resenas", __name__)


# GET /peliculas/{id}/resenas: público, con promedio y total.
@resenas_bp.route("/peliculas/<int:pelicula_id>/resenas", methods=["GET"])
def obtener_resenas(pelicula_id):
    limit, offset = validar_paginacion(request.args)
    return jsonify(resenas_service.listar_resenas(pelicula_id, limit, offset)), 200


# POST /peliculas/{id}/resenas: solo clientes con una entrada ya validada de esa película.
@resenas_bp.route("/peliculas/<int:pelicula_id>/resenas", methods=["POST"])
@requiere_rol("cliente")
def crear_resena(pelicula_id):
    calificacion, comentario = validar_body_resena(request.get_json(silent=True))
    resena = resenas_service.crear_resena(
        int(g.usuario["id"]), pelicula_id, calificacion, comentario
    )
    return jsonify(resena), 201


# GET /peliculas/{id}/resenas/estado: le dice al cliente si puede reseñar.
@resenas_bp.route("/peliculas/<int:pelicula_id>/resenas/estado", methods=["GET"])
@requiere_rol("cliente")
def estado_resena(pelicula_id):
    return jsonify(resenas_service.estado_usuario(int(g.usuario["id"]), pelicula_id)), 200

    

# GET /usuarios/me/resenas: las reseñas del cliente autenticado.
@resenas_bp.route("/usuarios/me/resenas", methods=["GET"])
@requiere_rol("cliente")
def obtener_mis_resenas():
    limit, offset = validar_paginacion(request.args)
    return jsonify(
        resenas_service.listar_resenas_usuario(int(g.usuario["id"]), limit, offset)
    ), 200


