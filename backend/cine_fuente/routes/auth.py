from flask import Blueprint, jsonify, request

from cine_fuente.services import auth as auth_service
from cine_fuente.utils import respuesta_error_excepcion, respuesta_error_interno
from cine_fuente.validators.auth import validar_body_login

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/login", methods=["POST"])
def post_login():
    try:
        credenciales = validar_body_login(request.get_json(silent=True))
        return jsonify(auth_service.iniciar_sesion(credenciales)), 200
    except ValueError as error:
        return respuesta_error_excepcion(error)
    except Exception as error:
        return respuesta_error_interno(error)
