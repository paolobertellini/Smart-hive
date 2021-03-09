from flask import render_template

from app import blueprint
from server import login_manager


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('errors/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('login-register/login.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('errors/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('errors/page-500.html'), 500
