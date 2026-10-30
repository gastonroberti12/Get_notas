from flask import Blueprint, render_template

users_bp = Blueprint("users", __name__)


@users_bp.route("/login")
def login():
    return render_template("login.html")


@users_bp.route("/perfil")
def profile():
    return render_template("perfil.html")