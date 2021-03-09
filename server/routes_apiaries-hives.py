# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, redirect, request, url_for, flash
from flask_login import (
    current_user,
    login_required
)

from app import blueprint
from app.forms import CreateApiaryForm, CreateHiveForm
from database.models import ApiaryModel, HiveModel, SensorFeed
from server import db
from utility.weather import weather

from datetime import datetime

# ----------------- APIARY ----------------- #

@blueprint.route('/apiaries', methods=['POST', 'GET'])
@login_required
def apiaries():
    apiaries = ApiaryModel.query.filter_by(user_id=current_user.username).all()
    apiary_form = CreateApiaryForm(request.form)
    if 'new_apiary' in request.form:

        # read form data
        id_apiary = request.form['id_apiary']
        id_user = current_user.username
        location = request.form['location']
        apiary = ApiaryModel(apiary_id=id_apiary, user_id=id_user, location=location)
        try:
            db.session.add(apiary)
            db.session.commit()
        except Exception as e:
            flash("You already have an apiary called: " + id_apiary)
            return redirect(url_for('home_blueprint.apiaries'))
        # Locate user
        # user = User.query.filter_by(username=username).first()

        # Something (user or pass) is not ok
        return redirect(url_for('home_blueprint.apiaries'))

    if not current_user.is_authenticated:
        return render_template('apiaries.html', form=apiary_form, apiaries=apiaries)
    return render_template('apiaries.html', form=apiary_form, apiaries=apiaries)


@blueprint.route('/removeApiary', methods=['GET'])
@login_required
def removeApiary():
    to_remove = request.args['to_remove']
    apiary_to_remove = ApiaryModel.query.filter_by(apiary_id=to_remove, user_id=current_user.username).first()
    hives_to_remove = HiveModel.query.filter_by(apiary_id=to_remove, user_id=current_user.username).all()
    for el in hives_to_remove:
        db.session.delete(el)
        data_to_modify = SensorFeed.query.filter_by(hive_id=el.hive_id).all()
        for x in data_to_modify:
            x.hive_id = ''
    db.session.delete(apiary_to_remove)
    db.session.commit()
    return redirect(url_for('home_blueprint.apiaries'))


# ----------------- HIVE ----------------- #


@blueprint.route('/hive', methods=['POST', 'GET'])
@login_required
def hive():
    apiaries = db.session.query(ApiaryModel.apiary_id).filter_by(user_id=current_user.username).all()
    ids = []
    for el in apiaries:
        ids.append(el.apiary_id)
    hive_form = CreateHiveForm(request.form)
    hive_form.id_apiary.choices = ids
    apiary_selected = request.args["apiary"]
    hives = HiveModel.query.filter_by(user_id=current_user.username, apiary_id=apiary_selected).all()
    if 'new_hive' in request.form:
        user_id = current_user.username
        hive_description = request.form['hive_description']
        association_code = request.form['association_code']
        apiary_selected = hive_form.id_apiary.data
        n_supers = request.form['n_supers']

        if (apiary_selected == ""):
            flash("Select an Apiary before to insert a new hive")
            return redirect(url_for('home_blueprint.hive', apiary=apiary_selected))
        hive = HiveModel(apiary_id=apiary_selected, user_id=user_id, hive_description=hive_description,
                         association_code=association_code, n_supers=n_supers)
        if (db.session.query(HiveModel.hive_id).filter_by(association_code=hive.association_code).scalar() is not None):
            flash("Control the correctness of the association code or contact the assistence.")
            return redirect(url_for('home_blueprint.hive', apiary=apiary_selected))
        if (db.session.query(HiveModel.hive_id).filter_by(apiary_id=hive.apiary_id,
                                                          hive_description=hive_description,
                                                          user_id=user_id).scalar() is not None):
            flash("Hive description already used in this apiary. Please try again.")
            return redirect(url_for('home_blueprint.hive', apiary=apiary_selected))
        else:
            db.session.add(hive)
            db.session.commit()

        return redirect(url_for('home_blueprint.hive', apiary=apiary_selected))

    if not current_user.is_authenticated:
        return render_template('hive.html', form=hive_form, hives=hives, apiaries=apiaries)
    return render_template('hive.html', form=hive_form, hives=hives, apiaries=apiaries, apiary=apiary_selected)


@blueprint.route('/removeHive', methods=['GET'])
@login_required
def removeHive():
    to_remove = request.args['to_remove']
    apiary = request.args['apiary']
    hives_to_remove = HiveModel.query.filter_by(hive_id=to_remove, user_id=current_user.username).first()
    data_to_modify = SensorFeed.query.filter_by(hive_id=hives_to_remove.hive_id).all()
    db.session.delete(hives_to_remove)
    for x in data_to_modify:
        x.hive_id = ''
    db.session.commit()
    return redirect(url_for('home_blueprint.hive', apiary=apiary))


# ----------------- SENSOR FEED AND DASHBOARD CONTROLLER ----------------- #


@blueprint.route('/sensorFeed', methods=['POST', 'GET'])
@login_required
def sensorFeed():
    hive = request.args["hive_id"]
    apiary_id = HiveModel.query.filter_by(hive_id=hive).first().apiary_id
    elenco = SensorFeed.query.filter_by(hive_id=hive).all()

    return render_template('sensor-feed.html', lista=elenco, apiary=apiary_id)


@blueprint.route('/dashboard', methods=['POST', 'GET'])
@login_required
def dashboard():
    hive_id = request.args["hive_id"]
    apiary = request.args["apiary"]

    sf = SensorFeed.query.filter_by(hive_id=hive_id).all()
    loc = ApiaryModel.query.filter_by(apiary_id=apiary).first().location
    hive = HiveModel.query.filter_by(hive_id=hive_id).first()
    entrance = hive.entrance
    alarm = hive.alarm
    w = {"temp": weather(loc)['temperature']['temp'], "status": weather(loc)['status']}
    honey_prod = (sf[-1].weight * 100) / ((hive.n_supers * 30) + 50)
    min = (datetime.now() - sf[-1].timestamp).total_seconds() / 60.0
    if (min > 1):
        time = False
    else:
        time = True

    dashboard = {"hive":hive, "apiary":apiary, "sf":sf, "time":time, "sf":sf, "loc":loc, "w":w, "hp":int(honey_prod) }

    if request.args["type"] == "alarm":
        alarm = not alarm
        db.session.query(HiveModel).filter(HiveModel.hive_id == hive_id).update({'alarm': alarm})
        db.session.commit()
    if request.args["type"] == "entrance":
        entrance = not entrance
        db.session.query(HiveModel).filter(HiveModel.hive_id == hive_id).update({'entrance': entrance})
        db.session.commit()





    try:
        return render_template('dashboard.html', d=dashboard, type="none")
    except:
        flash("There are no data belonging to this specific hive.")
        return redirect(url_for('home_blueprintx.hive', hive_id=hive_id, apiary=apiary))
