from functools import wraps
from flask import session, redirect, url_for

ROL_ADMIN = 'administrador'
ROL_CLIENTE = 'cliente'


def esta_logueado():
    return 'usuario' in session


def es_admin():
    return session.get('usuario', {}).get('rol') == ROL_ADMIN

def solo_admin(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not es_admin():
            return redirect(url_for("peliculas.inicio"))
        return vista(*args, **kwargs)
    return envoltura

def es_cliente():
    return session.get('usuario', {}).get('rol') == ROL_CLIENTE