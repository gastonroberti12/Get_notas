from flask import Blueprint, request, jsonify, make_response,

from cine_fuente.services import usuarios as usuarios_service
from cine_fuente.utils import (
    requiere_token,
    respuesta_error_excepcion,
    respuesta_error_interno,
    respuesta_paginada,
    validar_paginacion,
)
from cine_fuente.validators import validar_filtros_usuarios, validar_body_crear_usuario, validar_id_usuario

usuarios_bp = Blueprint("usuarios", __name__)


# Endpoint GET /usuarios: listado paginado para el administrador, filtrable por rol, nombre y email.
@usuarios_bp.route("/usuarios", methods=["GET"])
@requiere_token(("administrador",))
def get_usuarios():
    try:
        filtros = validar_filtros_usuarios(request.args)
        limit, offset = validar_paginacion(request.args)
        usuarios, total = usuarios_service.listar_usuarios(filtros, limit, offset)
        return respuesta_paginada("usuarios", usuarios, total, limit, offset)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    except Exception:
        return respuesta_error_interno()


# Endpoint POST /usuarios: registra un usuario con rol cliente.
@usuarios_bp.route("/usuarios", methods=["POST"])
def post_usuario():
    try:
        datos = validar_body_crear_usuario(request.get_json(silent=True))
        usuario_id = usuarios_service.crear_usuario(datos)
        respuesta = make_response(jsonify({"id": usuario_id}), 201)
        respuesta.headers["Location"] = f"/usuarios/{usuario_id}"
        return respuesta
    except ValueError as error:
        return respuesta_error_excepcion(error)
    except Exception:
        return respuesta_error_interno()


# Endpoint GET /usuarios/{id}: el administrador ve cualquier usuario; el cliente, solo el propio.
@usuarios_bp.route("/usuarios/<id_usuario>", methods=["GET"])
@requiere_token(("administrador", "cliente"))
def get_usuario(id_usuario):
    try:
        id_usuario = validar_id_usuario(id_usuario)
        return jsonify(usuarios_service.obtener_usuario(id_usuario)), 200
    except ValueError as error:
        return respuesta_error_excepcion(error)
    except Exception as error:
        return respuesta_error_interno(error)

# Endpoint GET /usuarios/me: devuelve el perfil del usuario autenticado.
@usuarios_bp.route("/usuarios/me", methods=["GET"])
@requiere_token(("cliente", "administrador"))
def get_mi_perfil():
    try:
        return jsonify(usuarios_service.obtener_perfil(int(g.usuario["id"]))), 200
    except ValueError as error:
        return respuesta_error_excepcion(error)
    except Exception as error:
        return respuesta_error_interno(error) 