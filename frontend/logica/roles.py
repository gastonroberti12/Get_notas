from functools import wraps
from flask import session, redirect, request, url_for

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

def solo_logueado(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not esta_logueado():
            siguiente = request.full_path.rstrip('?') if request.method == 'GET' else None #es la ruta con sus parametros
            return redirect(url_for('users.login', next=siguiente))
        return vista(*args, **kwargs)
    return envoltura

def es_cliente():
    return session.get('usuario', {}).get('rol') == ROL_CLIENTE