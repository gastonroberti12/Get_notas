from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name('.env'), override=False)

from flask import Flask, jsonify
from cine_fuente.utils import construir_error_api
from cine_fuente.routes.funciones import funciones_bp
from cine_fuente.routes.butacas import butacas_bp
from cine_fuente.routes.servicios import servicios_bp
from cine_fuente.routes.peliculas import peliculas_bp
from cine_fuente.routes.reservas import reservas_bp
from cine_fuente.routes.usuarios import usuarios_bp
from cine_fuente.routes.salas import salas_bp
from cine_fuente.routes.sucursales import sucursales_bp


def crear_app():
    app = Flask(__name__)
    app.register_blueprint(peliculas_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(funciones_bp)
    app.register_blueprint(sucursales_bp)
    app.register_blueprint(salas_bp)
    app.register_blueprint(butacas_bp)
    app.register_blueprint(servicios_bp)

    @app.errorhandler(404)
    def manejar_ruta_no_encontrada(error):
        return jsonify(construir_error_api('resource.not.found', 'Recurso no encontrado', 'La URL solicitada no existe.')), 404

    @app.errorhandler(405)
    def manejar_metodo_no_permitido(error):
        return jsonify(construir_error_api('method.not.allowed', 'Método no permitido', 'El método HTTP usado no está soportado por esta URL.')), 405

    @app.errorhandler(ValueError)
    def manejar_error_validacion(error):
        respuesta = error.args[0] if error.args else construir_error_api('invalid.body', 'Datos inválidos', 'Los datos enviados no son válidos.')
        return jsonify(respuesta), 400

    @app.errorhandler(500)
    def manejar_error_interno(error):
        return jsonify(construir_error_api('internal.error', 'Error interno del servidor', 'No se pudo completar la operación.')), 500

    return app


app = crear_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
