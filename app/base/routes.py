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
from app.base.forms import LoginForm, CreateAccountForm, CreateApiaryForm, CreateHiveForm
from app.base.models import ApiaryModel, User, HiveModel, SensorFeed

from app.base.util import verify_pass

@blueprint.route('/')
def route_default():
    return redirect(url_for('home_blueprint.index'))

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
        return render_template( 'accounts/login.html', form=login_form)
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
    return redirect(url_for('home_blueprint.index'))

@blueprint.route('/shutdown')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'


@blueprint.route('/new_apiary',methods=['POST', 'GET'])
def new_apiary():
    elenco = ApiaryModel.query.filter_by(user_id = current_user.username).all()
    apiary_form = CreateApiaryForm(request.form)
    if 'new_apiary' in request.form:

        # read form data
        id_apiary = request.form['id_apiary']
        id_user = current_user.username

        apiary = ApiaryModel(apiary_id=id_apiary, user_id=id_user)
        db.session.add(apiary)
        db.session.commit()

        # Locate user
        # user = User.query.filter_by(username=username).first()

        # Something (user or pass) is not ok
        return redirect(url_for('base_blueprint.new_apiary'))

    if not current_user.is_authenticated:
        return render_template('new_apiary.html', form=apiary_form, lista = elenco)
    return render_template('new_apiary.html', form=apiary_form, lista = elenco)

@blueprint.route('/hive',methods=['POST', 'GET'])
@login_required
def hive():
    elenco = HiveModel.query.filter_by(user_id = current_user.username).all()
    hive_form = CreateHiveForm(request.form)
    apiary_id = request.args['apiary']
    if 'new_hive' in request.form:

        # read form dat
        user_id = current_user.username
        hive_description = request.form['hive_description']
        association_code = request.form['association_code']
        # id_apiary= request.form['id_apiary']
        hive = HiveModel(apiary_id=apiary_id, user_id=user_id, hive_description= hive_description, association_code= association_code)
        db.session.add(hive)
        db.session.commit()

        return redirect(url_for('base_blueprint.hive', apiary = apiary_id))

    if not current_user.is_authenticated:
        return render_template('hive.html', form=hive_form, lista = elenco, apiary = apiary_id)
    return render_template('hive.html', form=hive_form, lista = elenco, apiary = apiary_id)

# @blueprint.route('/new_apiary',methods=['POST', 'GET'])
# @login_required
# def new_apiary():
#     if request.method == 'POST':
#         if request.form.get("Aggiungi_Apiario") == "Add apiary":
#             apiary_id = request.form['nuovoApiario']
#             user = current_user.email
#             apiario = ApiaryModel(apiary_id=apiary_id, user_id=user)
#             try:
#                 db.session.add(apiario)
#                 db.session.commit()
#             except Exception as e:
#                 flash("You already have an apiary called: " + apiary_id)
#                 return redirect(url_for('new_apiary'))
#
#             return render_template('aggiungiApiario.html')
#
#     return render_template('aggiungiApiario.html')


## Errors

# @blueprint.route('/sensorfeed',methods=['POST', 'GET'])
# @login_required
# def hive():
#     elenco = SensorFeed.query.filter_by(hive_id = current_user.username).all()
#     hive_form = CreateHiveForm(request.form)
#     apiary_id = request.args['apiary']
#     if 'new_hive' in request.form:
#
#         # read form dat
#         user_id = current_user.username
#         hive_description = request.form['hive_description']
#         association_code = request.form['association_code']
#         # id_apiary= request.form['id_apiary']
#         hive = HiveModel(apiary_id=apiary_id, user_id=user_id, hive_description= hive_description, association_code= association_code)
#         db.session.add(hive)
#         db.session.commit()
#
#         return redirect(url_for('base_blueprint.hive', apiary = apiary_id))
#
#     if not current_user.is_authenticated:
#         return render_template('hive.html', form=hive_form, lista = elenco, apiary = apiary_id)
#     return render_template('hive.html', form=hive_form, lista = elenco, apiary = apiary_id)


@blueprint.route('/new-sensor-feed', methods=['GET','POST'])
# @login_required
def newSensorFeed():
    req = request.get_json(force=True)
    hive_id = HiveModel.query.filter_by(association_code=req['association_code']).first().hive_id

    if (hive_id is not None):
        user_id = HiveModel.query.filter_by(hive_id=hive_id).first().user_id
        apiary_id = HiveModel.query.filter_by(hive_id=hive_id).first().apiary_id
        sensorFeed = SensorFeed(hive_id=req['hive_id'],
                                temperature=req['temperature'],
                                humidity=req['humidity'],
                                weight=req['weight'])
        db.session.add(sensorFeed)
        db.session.commit()
        return ({'hive_id': hive_id, 'user_id': user_id, 'apiary_id': apiary_id})
    else:
        return ({'hive_id': None, 'user_id': None, 'apiary_id': None})

@blueprint.route('/sensorFeed',methods=['POST', 'GET'])
@login_required
def sensorFeed():

    apiary_id = HiveModel.query.filter_by(hive_id="1").first().apiary_id
    elenco = SensorFeed.query.filter_by(hive_id="1").all()

    return render_template('sensor-feed.html',lista = elenco, apiary = apiary_id)

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
