import os
from dotenv import load_dotenv
from flask import Flask, render_template
from routes.products import peliculas_bp
from routes.cines import cines_bp
from routes.users import users_bp
from routes.backoffice import backoffice_bp
from routes.roles import esta_logueado, es_admin, es_cliente
from manejo_errorers import registrar_error_handlers

load_dotenv()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.environ['SECRET_KEY']

    app.register_blueprint(peliculas_bp)
    app.register_blueprint(cines_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(backoffice_bp)

    registrar_error_handlers(app)

    
    # Context processors para que las funciones de roles estén disponibles en todas las plantillas. esto le pasa al render_template el rol segun lo q tenga el template
    app.context_processor(lambda: {'esta_logueado': esta_logueado, 'es_admin': es_admin, 'es_cliente': es_cliente})

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errores/404.html"), 404

    @app.errorhandler(500)
    def internar_server_error(error):
        return render_template("errores/500.html"), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("errores/403.html"), 403

    @app.errorhandler(503)
    def service_unavailable(error):
        return render_template("errores/503.html"), 503

    @app.errorhandler(405)
    def method_not_allowed(error):
        return render_template("errores/405.html"), 405
    
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)