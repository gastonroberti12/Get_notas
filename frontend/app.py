from flask import Flask
from Routes.products import peliculas_bp
from Routes.cines import cines_bp
from Routes.users import users_bp

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.register_blueprint(peliculas_bp)
    app.register_blueprint(cines_bp)
    app.register_blueprint(users_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)