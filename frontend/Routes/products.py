from flask import Blueprint, render_template


peliculas_bp = Blueprint("peliculas", __name__)


@peliculas_bp.route("/")
def inicio():
    return render_template("index.html")

@peliculas_bp.route("/cartelera")
def cartelera():
    return render_template("cartelera.html")