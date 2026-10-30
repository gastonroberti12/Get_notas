from flask import session

ROL_ADMIN = 'administrador'
ROL_CLIENTE = 'cliente'


def esta_logueado():
    return 'usuario' in session


def es_admin():
    return session.get('usuario', {}).get('rol') == ROL_ADMIN


def es_cliente():
    return session.get('usuario', {}).get('rol') == ROL_CLIENTE