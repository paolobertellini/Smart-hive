# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import jsonify, render_template, redirect, request, url_for
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)

from app import db, login_manager
from app.base import blueprint
from app.base.forms import LoginForm, CreateAccountForm, CreateApiaryForm
from app.base.models import ApiaryModel, User

from app.base.util import verify_pass

@blueprint.route('/')
def route_default():
    return redirect(url_for('base_blueprint.login'))

## Login & Registration

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
        if user and verify_pass( password, user.password):

            login_user(user)
            return redirect(url_for('base_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template( 'accounts/login.html', msg='Wrong user or password', form=login_form)

    if not current_user.is_authenticated:
        return render_template( 'accounts/login.html',
                                form=login_form)
    return redirect(url_for('home_blueprint.index'))

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    login_form = LoginForm(request.form)
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username  = request.form['username']
        email     = request.form['email'   ]

        # Check usename exists
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template( 'accounts/register.html', 
                                    msg='Username already registered',
                                    success=False,
                                    form=create_account_form)

        # Check email exists
        user = User.query.filter_by(email=email).first()
        if user:
            return render_template( 'accounts/register.html', 
                                    msg='Email already registered', 
                                    success=False,
                                    form=create_account_form)

        # else we can create the user
        user = User(**request.form)
        db.session.add(user)
        db.session.commit()

        return render_template( 'accounts/register.html', 
                                msg='User created please <a href="/login">login</a>', 
                                success=True,
                                form=create_account_form)

    else:
        return render_template( 'accounts/register.html', form=create_account_form)

@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('base_blueprint.login'))

@blueprint.route('/shutdown')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'


@blueprint.route('/new_apiary',methods=['POST', 'GET'])
def new_apiary():
    apiary_form = CreateApiaryForm(request.form)
    if 'new_apiary' in request.form:

        # read form data
        id_apiary = request.form['id_apiary']
        id_user = request.form['id_user']

        apiary = ApiaryModel(id_apiario=id_apiary, id_utente=id_user)
        db.session.add(apiary)
        db.session.commit()

        # Locate user
        # user = User.query.filter_by(username=username).first()

        # Something (user or pass) is not ok
        return render_template('transactions.html', msg="You already have an apiary called: " + id_apiary, form=apiary_form)

    if not current_user.is_authenticated:
        return render_template('transactions.html', form=apiary_form)
    return render_template('transactions.html', form=apiary_form)

# @blueprint.route('/new_apiary',methods=['POST', 'GET'])
# @login_required
# def new_apiary():
#     if request.method == 'POST':
#         if request.form.get("Aggiungi_Apiario") == "Add apiary":
#             id_apiario = request.form['nuovoApiario']
#             user = current_user.email
#             apiario = ApiaryModel(id_apiario=id_apiario, id_utente=user)
#             try:
#                 db.session.add(apiario)
#                 db.session.commit()
#             except Exception as e:
#                 flash("You already have an apiary called: " + id_apiario)
#                 return redirect(url_for('new_apiary'))
#
#             return render_template('aggiungiApiario.html')
#
#     return render_template('aggiungiApiario.html')


## Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('page-403.html'), 403

@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('page-403.html'), 403

@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('page-404.html'), 404

@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('page-500.html'), 500
