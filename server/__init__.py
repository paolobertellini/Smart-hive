# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from importlib import import_module

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)


def register_blueprints(app):
    for module_name in ('template', 'apiaries-hives', 'login-register', 'services', 'errors'):
        module = import_module('server.routes_{}'.format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app):
    @app.before_first_request
    def initialize_database():
        with app.app_context():
            db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def create_app(config):
    app = Flask(__name__, root_path='Smart-hive', static_folder='./app')
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)

    return app
