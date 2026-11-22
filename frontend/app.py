import os
from dotenv import load_dotenv
from flask import Flask
from routes.peliculas import peliculas_bp
from routes.cines import cines_bp
from routes.users import users_bp
from routes.backoffice.backoffice import backoffice_bp
from routes.purchases import purchases_bp
from logica.roles import esta_logueado, es_admin, es_cliente
from routes.errores import errores_bp
from logica.sucursales import contexto_sucursales

load_dotenv()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.environ['SECRET_KEY']

    app.register_blueprint(peliculas_bp)
    app.register_blueprint(cines_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(backoffice_bp)
    app.register_blueprint(purchases_bp)
    app.register_blueprint(errores_bp)

    # Expone sucursales y sucursal_actual a todas las plantillas que se renderizan
    app.context_processor(lambda: dict(zip(("sucursales", "sucursal_actual"), contexto_sucursales())))
    
    # Expone las funciones de roles a todas las plantillas, para mostrar u ocultar partes segun el rol
    app.context_processor(lambda: {'esta_logueado': esta_logueado, 'es_admin': es_admin, 'es_cliente': es_cliente})
    
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
