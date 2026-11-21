from flask import g, session
from services.sucursales import listar_sucursales

# Regla de la sucursal elegida: la de la sesión o, si no hay una válida, la principal (menor id)


def contexto_sucursales():
    # se guarda en g para consultar al backend una sola vez por request.
    if 'sucursales' not in g:
        _, datos = listar_sucursales()  # si llega a fallar, datos no trae 'sucursales' y queda la lista vacia
        g.sucursales = datos.get('sucursales', [])
        elegida = None
        principal = None
        for sucursal in g.sucursales:
            if principal is None or sucursal['id'] < principal['id']:
                principal = sucursal
            if sucursal['id'] == session.get('sucursal_id'):
                elegida = sucursal
        # Si no hay una elegida valida, usa la principal
        g.sucursal_actual = elegida or principal
        if g.sucursal_actual:
            session['sucursal_id'] = g.sucursal_actual['id']
    return g.sucursales, g.sucursal_actual


def filtro_sucursal():
    # filtro para los listados del backend
    _, actual = contexto_sucursales()
    if actual is None:
        return ''
    return f"&sucursal_id={actual['id']}"