from flask import render_template


def registrar_error_handlers(app):

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("errores/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errores/404.html"), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return render_template("errores/405.html"), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template("errores/500.html"), 500

    @app.errorhandler(503)
    def service_unavailable(error):
        return render_template("errores/503.html"), 503