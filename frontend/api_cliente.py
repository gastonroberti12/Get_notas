import os
import requests
from flask import session

API_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1:5001')

MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor.'
MENSAJE_GENERICO = 'Ocurrió un error inesperado.'


def llamar_api(metodo, endpoint, datos=None):
    # Si hay sesion, manda el token en Authorization: Bearer.
    headers = {}
    if 'token' in session:
        headers['Authorization'] = f"Bearer {session['token']}"
    try:
        r = requests.request(metodo, f'{API_URL}{endpoint}', json=datos, headers=headers, timeout=5)
        return r.status_code, (r.json() if r.content else {})
    except (requests.RequestException, ValueError):
        return None, {}


def mensaje_error(status, cuerpo, MENSAJE_GENERICO):
    if status is None:
        return MENSAJE_SIN_CONEXION
    errores = cuerpo.get('errors') or [{}]
    return errores[0].get('mensaje', MENSAJE_GENERICO)