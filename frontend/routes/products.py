import os
import requests

from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for


peliculas_bp = Blueprint("peliculas", __name__)

API_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5001")


# Obtener listados del backend
def obtener_listado(endpoint, clave):

    resultados = []
    offset = 0
    limite = 100

    try:
        while True:

            respuesta = requests.get(
                f"{API_URL}/{endpoint}",
                params={"_limit": limite, "_offset": offset},
                timeout=5
            )

            if respuesta.status_code == 204:
                break

            if respuesta.status_code != 200:
                return [], "No se pudieron obtener los datos."

            datos = respuesta.json()

            resultados.extend(datos.get(clave, []))

            if "_next" not in datos.get("_links", {}):
                break

            offset += limite

    except (requests.RequestException, ValueError, TypeError):
        return [], "No se pudo conectar con el servidor."

    return resultados, None


# Página principal
@peliculas_bp.route("/")
def inicio():

    # Obtener películas del backend
    peliculas, error_peliculas = obtener_listado(
        "peliculas",
        "peliculas"
    )

    # Primeras cinco películas para el carrusel
    peliculas_destacadas = peliculas[:5]

    return render_template(
        "index.html",
        peliculas=peliculas,
        peliculas_destacadas=peliculas_destacadas,
        error_cartelera=error_peliculas
    )


# Redirección a la cartelera
@peliculas_bp.route("/cartelera")
def cartelera():

    return redirect(
        url_for("peliculas.inicio", _anchor="cartelera")
    )


# Página con el catálogo completo
@peliculas_bp.route("/peliculas")
def listado_peliculas():

    peliculas, error_peliculas = obtener_listado(
        "peliculas",
        "peliculas"
    )

    return render_template(
        "peliculas.html",
        peliculas=peliculas,
        error_peliculas=error_peliculas
    )