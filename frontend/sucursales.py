from flask import g, session
from api_cliente import llamar_api

def obtener_sucursales():
    status, datos = llamar_api("GET", "/sucursales?_limit=100")
    return datos.get("sucursales", []) if status == 200 else []


# Lo que devuelve los guarda en g para consultar al back una sola vez por request.
# La actual es la elegida en la session.
def contexto_sucursales():
    if "sucursales" not in g:
        g.sucursales = obtener_sucursales()
        elegida = None
        principal = None
        for sucursal in g.sucursales:
            if principal is None or sucursal["id"] < principal["id"]:
                principal = sucursal
            if sucursal["id"] == session.get("sucursal_id"):
                elegida = sucursal
        # Si no hay una elegida válida, usa la principal
        g.sucursal_actual = elegida or principal
        if g.sucursal_actual:
            session["sucursal_id"] = g.sucursal_actual["id"]
    return g.sucursales, g.sucursal_actual
