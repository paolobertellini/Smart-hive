# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import jsonify, render_template, redirect, request, url_for, flash
from weather import weather
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

@blueprint.context_processor
def inject_apiaries():
    if current_user.is_authenticated:
        apiaries = ApiaryModel.query.filter_by(user_id=current_user.username).all()
    else:
        apiaries=""

    def find_hives(apiary):
        hives = HiveModel.query.filter_by(user_id=current_user.username, apiary_id=apiary).all()
        return hives
    return dict(apiaries=apiaries, find_hives= find_hives)



@blueprint.route('/new_apiary',methods=['POST', 'GET'])
def new_apiary():
    apiaries= ApiaryModel.query.filter_by(user_id = current_user.username).all()
    apiary_form = CreateApiaryForm(request.form)
    if 'new_apiary' in request.form:

        # read form data
        id_apiary = request.form['id_apiary']
        id_user = current_user.username
        location = request.form['location']
        apiary = ApiaryModel(apiary_id=id_apiary, user_id=id_user, location = location )
        try:
            db.session.add(apiary)
            db.session.commit()
        except Exception as e:
            flash("You already have an apiary called: " + id_apiary)
            return redirect(url_for('base_blueprint.new_apiary'))
        # Locate user
        # user = User.query.filter_by(username=username).first()

        # Something (user or pass) is not ok
        return redirect(url_for('base_blueprint.new_apiary'))

    if not current_user.is_authenticated:
        return render_template('new_apiary.html', form=apiary_form, apiaries= apiaries)
    return render_template('new_apiary.html', form=apiary_form,apiaries= apiaries)

@blueprint.route('/hive',methods=['POST', 'GET'])
@login_required
def hive():
    apiaries= ApiaryModel.query.filter_by(user_id = current_user.username).all()
    hive_form = CreateHiveForm(request.form)
    apiary_selected= request.args["apiary"]
    hives = HiveModel.query.filter_by(user_id = current_user.username,apiary_id=apiary_selected).all()
    if 'new_hive' in request.form:

        # read form dat
        user_id = current_user.username
        hive_description = request.form['hive_description']
        association_code = request.form['association_code']
        if(apiary_selected==""):
            flash("Select an Apiary before to insert a new hive")
            return redirect(url_for('base_blueprint.hive',apiary = apiary_selected))
        hive = HiveModel(apiary_id=apiary_selected, user_id=user_id, hive_description= hive_description, association_code= association_code)
        if (db.session.query(HiveModel.hive_id).filter_by(association_code=hive.association_code).scalar() is not None):
            flash("Control the correctness of the association code or contact the assistence.")
            return redirect(url_for('base_blueprint.hive', apiary=apiary_selected))
        if (db.session.query(HiveModel.hive_id).filter_by(apiary_id=hive.apiary_id,
                                                            hive_description=hive_description,
                                                            user_id=user_id).scalar() is not None):
            flash("Hive description already used in this apiary. Please try again.")
            return redirect(url_for('base_blueprint.hive', apiary=apiary_selected))
        else:
            db.session.add(hive)
            db.session.commit()

        return redirect(url_for('base_blueprint.hive', apiary=apiary_selected))

    if not current_user.is_authenticated:
        return render_template('hive.html', form=hive_form, hives = hives, apiaries= apiaries)
    return render_template('hive.html', form=hive_form, hives = hives, apiaries= apiaries,apiary=apiary_selected)

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
    hive = request.args["hive_id"]

    # apiary_id = HiveModel.query.filter_by(hive_id="2").first().apiary_id
    elenco = SensorFeed.query.filter_by(hive_id=hive).all()

    return render_template('sensor-feed.html',lista = elenco)

@blueprint.route('/dashboard',methods=['POST', 'GET'])
@login_required
def dashboard():
    hive = request.args["hive"]
    apiary = request.args["apiary"]
    sf = SensorFeed.query.filter_by(hive_id=hive).all()
    # elenco = SensorFeed.query.filter_by(hive_id="1").all()
    location = ApiaryModel.query.filter_by(apiary_id=apiary).first().location
    w= "It is currently " + str(weather(location)['temperature']['temp']) + " °C and " + str(weather(location)['status'])
    return render_template('dashboard.html', SensorFeed = sf, hive_id = hive, weather= w, location= location)

@blueprint.route('/removeApiary',methods=['GET'])
@login_required
def removeApiary():
    to_remove = request.args['to_remove']
    apiary_to_remove = ApiaryModel.query.filter_by(apiary_id=to_remove, user_id = current_user.username).first()
    hives_to_remove = HiveModel.query.filter_by(apiary_id=to_remove, user_id=current_user.username).all()
    for el in hives_to_remove:
        db.session.delete(el)
        data_to_modify = SensorFeed.query.filter_by(hive_id=el.hive_id).all()
        for x in data_to_modify:
            x.hive_id=''
    db.session.delete(apiary_to_remove)
    db.session.commit()
    return redirect(url_for('base_blueprint.new_apiary'))


@blueprint.route('/removeHive', methods=['GET'])
@login_required
def removeHive():
    to_remove = request.args['to_remove']
    apiary = request.args['apiary']
    hives_to_remove = HiveModel.query.filter_by(hive_id=to_remove, user_id=current_user.username).first()
    data_to_modify = SensorFeed.query.filter_by(hive_id=hives_to_remove.hive_id).all()
    db.session.delete(hives_to_remove)
    for x in data_to_modify:
        x.hive_id=''
    db.session.commit()
    return redirect(url_for('base_blueprint.hive', apiary = apiary))

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
