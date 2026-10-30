import os
from dotenv import load_dotenv
from flask import Flask
from Routes.products import peliculas_bp
from Routes.cines import cines_bp
from Routes.users import users_bp

load_dotenv()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.environ['SECRET_KEY']

    app.register_blueprint(peliculas_bp)
    app.register_blueprint(cines_bp)
    app.register_blueprint(users_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)