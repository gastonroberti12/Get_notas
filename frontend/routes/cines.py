from flask import Blueprint, render_template

cines_bp = Blueprint("cines", __name__)

@cines_bp.route("/cines")
def listado():
    return render_template("cines.html")