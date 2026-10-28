from flask import Blueprint


peliculas_bp = Blueprint("peliculas", __name__)


@peliculas_bp.route("/")
def inicio():
    return "Cine Paradiso - Frontend funcionando"