from flask import Flask
from Routes.products import peliculas_bp


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.register_blueprint(peliculas_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)