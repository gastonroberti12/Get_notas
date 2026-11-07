from flask import render_template, redirect, url_for, request
from api_cliente import llamar_api, mensaje_error
from routes.roles import es_admin
from routes.backoffice.backoffice import backoffice_bp


@backoffice_bp.route("/backoffice/validar-qr", methods=["GET", "POST"])
def validar_qr_admin():
    if not es_admin():
        return redirect(url_for("peliculas.inicio"))

    resultado = None
    if request.method == "POST":
        codigo = request.form.get("codigo_qr", "").strip()
        status, cuerpo = llamar_api("POST", "/entradas/validacion", {"codigo_qr": codigo})
        ok = status == 200
        resultado = {
            "ok": ok,
            "mensaje": (f"Entrada {cuerpo.get('id')} válida. Ingreso autorizado." if ok
                        else mensaje_error(status, cuerpo, "No se pudo validar la entrada.")),
        }
    return render_template("backadmin/validar_qr.html", resultado=resultado)