from flask import Blueprint, render_template

errores_bp = Blueprint("errores", __name__)



@errores_bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template("errores/403.html"), 403

@errores_bp.app_errorhandler(404)
def page_not_found(error):
    return render_template("errores/404.html"), 404


@errores_bp.app_errorhandler(405)
def method_not_allowed(error):
    return render_template("errores/405.html"), 405


@errores_bp.app_errorhandler(500)
def internal_server_error(error):
    return render_template("errores/500.html"), 500


@errores_bp.app_errorhandler(503)
def service_unavailable(error):
    return render_template("errores/503.html"), 503