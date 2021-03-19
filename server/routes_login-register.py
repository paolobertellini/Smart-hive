from flask import render_template, redirect, request, url_for
from flask_login import (
    current_user,
    login_user,
    logout_user
)

from app import blueprint
from app.forms import LoginForm, CreateAccountForm
from database.models import User
from server import db
from utility.mail import send_email
from utility.util import verify_pass


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = User.query.filter_by(username=username).first()

        # Check the password
        if user and verify_pass(password, user.password):
            login_user(user)
            return redirect(url_for('home_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template('login-register/login.html', msg='Wrong user or password', form=login_form)

    if not current_user.is_authenticated:
        return render_template('login-register/login.html', form=login_form)
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    login_form = LoginForm(request.form)
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check usename exists
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template('login-register/register.html',
                                   msg='Username already registered',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        user = User.query.filter_by(email=email).first()
        if user:
            return render_template('login-register/register.html',
                                   msg='Email already registered',
                                   success=False,
                                   form=create_account_form)

        # else we can create the user
        user = User(username=username, email=email, password=password, idTelegram=None)
        db.session.add(user)
        db.session.commit()
        send_email("Welcome in smart hive", "Test", email)

        return render_template('login-register/register.html',
                               msg='User created please <a href="/login">login</a>',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('login-register/register.html', form=create_account_form)


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/shutdown')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'
