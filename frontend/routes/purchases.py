from flask import Blueprint, redirect, url_for, render_template, flash
from api_cliente import llamar_api, mensaje_error
from routes.roles import esta_logueado

purchases_bp = Blueprint("purchases", __name__)


@purchases_bp.route("/reservas/<int:reserva_id>/cancelar", methods=['POST'])
def cancelar_reserva(reserva_id):
    if not esta_logueado():
        return redirect(url_for('users.login'))
    # El back valida titularidad y la regla de 1 hora; si responde error, el perfil se recarga igual.
    status, cuerpo = llamar_api('PATCH', f'/reservas/{reserva_id}', {'estado': 'cancelada'})
    if status in (200, 204):
        flash('Reserva cancelada con éxito.', 'exito')
    else:
        flash(mensaje_error(status, cuerpo, 'No se pudo cancelar la reserva.'), 'error')
    return redirect(url_for('users.profile'))

# Solo maqueta visual: todavía sin datos del backend.
@purchases_bp.route("/funciones/<int:funcion_id>/butacas")
def seleccion_butacas(funcion_id):
    return render_template("seleccion_butacas.html", funcion_id=funcion_id)


@purchases_bp.route("/checkout")
def checkout():
    return render_template("checkout.html")