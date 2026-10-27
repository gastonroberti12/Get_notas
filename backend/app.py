from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from cine_fuente.routes.peliculas import peliculas_bp


load_dotenv(Path(__file__).with_name(".env"), override=False)


def create_app():
    app = Flask(__name__)
    app.register_blueprint(peliculas_bp)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
