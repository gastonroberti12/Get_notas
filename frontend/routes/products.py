import os
import requests

from flask import Blueprint, render_template

peliculas_bp = Blueprint("peliculas", __name__)

API_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5001")


@peliculas_bp.route("/")
def inicio():
    peliculas = []
    error_cartelera = None

    try:
        respuesta = requests.get(
            f"{API_URL}/api/peliculas", #CAMBIAR EL /API, HAY QUE SACARLO EN BACKEND TAMBIEN
            params={"_limit": 20, "_offset": 0},
            timeout=5
        )

        if respuesta.status_code == 200:
            datos = respuesta.json()
            peliculas = datos.get("peliculas", [])

        elif respuesta.status_code == 204:
            peliculas = []

        else:
            error_cartelera = "No se pudo cargar la cartelera."

    except (requests.RequestException, ValueError):
        error_cartelera = "No se pudo conectar con el servidor."

    peliculas_destacadas = peliculas[:5]

    return render_template(
        "index.html",
        peliculas=peliculas,
        peliculas_destacadas=peliculas_destacadas,
        error_cartelera=error_cartelera
    )


@peliculas_bp.route("/cartelera")
def cartelera():
    return render_template("cartelera.html")

