from flask import Blueprint, redirect, url_for
from api_cliente import llamar_api
from routes.roles import esta_logueado

purchases_bp = Blueprint("purchases", __name__)


@purchases_bp.route("/reservas/<int:reserva_id>/cancelar", methods=['POST'])
def cancelar_reserva(reserva_id):
    if not esta_logueado():
        return redirect(url_for('users.login'))
    # El back valida titularidad y la regla de 1 hora; si responde error, el perfil se recarga igual.
    llamar_api('PATCH', f'/reservas/{reserva_id}', {'estado': 'cancelada'})
    return redirect(url_for('users.profile'))