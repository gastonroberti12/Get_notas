import os
from dotenv import load_dotenv
from flask import Flask
from routes.products import peliculas_bp
from routes.cines import cines_bp
from routes.users import users_bp
from routes.backoffice import backoffice_bp
from routes.roles import esta_logueado, es_admin, es_cliente

load_dotenv()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.environ['SECRET_KEY']

    app.register_blueprint(peliculas_bp)
    app.register_blueprint(cines_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(backoffice_bp)
    
    # Context processors para que las funciones de roles estén disponibles en todas las plantillas. esto le pasa al render_template el rol segun lo q tenga el template
    app.context_processor(lambda: {'esta_logueado': esta_logueado, 'es_admin': es_admin, 'es_cliente': es_cliente})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)