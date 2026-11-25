from flask import render_template, request
from services.api_cliente import mensaje_error
from services.entradas import validar_entrada
from logica.roles import solo_admin
from routes.backoffice.backoffice import backoffice_bp


@backoffice_bp.route("/backoffice/validar-qr", methods=["GET", "POST"])
@solo_admin
def validar_qr_admin():
    resultado = None
    if request.method == "POST":
        codigo = request.form.get("codigo_qr", "").strip()
        status, cuerpo = validar_entrada(codigo)
        ok = status == 200
        resultado = {
            "ok": ok,
            "mensaje": ("Ingreso autorizado." if ok
                        else mensaje_error(status, cuerpo, "No se pudo validar la entrada.")),
            "detalle": cuerpo.get("detalle") if ok else None,
        }
    return render_template("backadmin/validar_qr.html", resultado=resultado)