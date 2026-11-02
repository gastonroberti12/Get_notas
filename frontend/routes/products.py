from flask import Blueprint, render_template, request, redirect, url_for
from api_cliente import llamar_api, mensaje_error


peliculas_bp = Blueprint("peliculas", __name__)

# Obtener listados del backend
def obtener_listado(endpoint, clave):
    status, datos = llamar_api("GET", f"/{endpoint}?_limit=100")

    if status not in (200, 204):
        return [], mensaje_error(status, datos, "No se pudieron obtener los datos.")

    # Con 204 el cuerpo viene vacío, así que devuelve una lista vacía.
    return datos.get(clave, []), None


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