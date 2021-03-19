# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from datetime import datetime, timedelta

from flask import flash, request, redirect, url_for
from flask import render_template
from flask_login import (
    current_user,
    login_required
)
from werkzeug.utils import secure_filename

from app import blueprint
from app.forms import CreateApiaryForm, CreateHiveForm, CreateSwarmEventForm
from config import ALLOWED_EXTENSIONS, sensorFeed_std_freq
from database.models import ApiaryModel, HiveModel
from database.models import SensorFeed, SwarmEvent, User, SwarmCommunication
from server import db
from utility.dataPrediction import honeyProductionPrediction
from utility.loadFromCSV import loadDataFromCSV
from utility.weather import weather


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ----------------- APIARY ----------------- #

@blueprint.route('/apiaries', methods=['POST', 'GET'])
@login_required
def apiaries():
    apiaries = ApiaryModel.query.filter_by(user_id=current_user.id).all()
    apiary_form = CreateApiaryForm(request.form)
    if 'new_apiary' in request.form:

        # read form data
        id_apiary = request.form['id_apiary']
        id_user = current_user.id
        location = request.form['location']
        apiary = ApiaryModel(apiary_id=id_apiary, user_id=id_user, location=location)
        try:
            db.session.add(apiary)
            db.session.commit()
        except Exception as e:
            flash("You already have an apiary called: " + id_apiary)
            return redirect(url_for('home_blueprint.apiaries'))
        # Locate user
        # user = User.query.filter_by(id=id).first()

        # Something (user or pass) is not ok
        return redirect(url_for('home_blueprint.apiaries'))

    if not current_user.is_authenticated:
        return render_template('apiaries.html', form=apiary_form, apiaries=apiaries)
    return render_template('apiaries.html', form=apiary_form, apiaries=apiaries)


@blueprint.route('/removeApiary', methods=['GET'])
@login_required
def removeApiary():
    to_remove = request.args['to_remove']
    apiary_to_remove = ApiaryModel.query.filter_by(apiary_id=to_remove, user_id=current_user.id).first()
    hives_to_remove = HiveModel.query.filter_by(apiary_id=to_remove, user_id=current_user.id).all()
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
    apiaries = db.session.query(ApiaryModel.apiary_id).filter_by(user_id=current_user.id).all()
    ids = []
    for el in apiaries:
        ids.append(el.apiary_id)
    hive_form = CreateHiveForm(request.form)
    hive_form.id_apiary.choices = ids
    apiary_selected = request.args["apiary"]
    hives = HiveModel.query.filter_by(apiary_id=apiary_selected).all()
    if 'new_hive' in request.form:

        hive_description = request.form['hive_description']
        association_code = request.form['association_code']
        apiary_selected = hive_form.id_apiary.data
        n_supers = request.form['n_supers']

        if (apiary_selected == ""):
            flash("Select an Apiary before to insert a new hive")
            return redirect(url_for('home_blueprint.hive', apiary=apiary_selected))

        hive = HiveModel(apiary_id=apiary_selected, hive_description=hive_description,
                         association_code=association_code, n_supers=n_supers, update_freq=sensorFeed_std_freq)

        file = request.files['file']
        if file != '':
            # if file.filename == '':
            #     flash('No selected file')
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(filename)
                loadDataFromCSV(filename)

        if db.session.query(HiveModel.hive_id).filter_by(association_code=hive.association_code).scalar() is not None:
            flash("Control the correctness of the association code or contact the assistence.")
            return redirect(url_for('home_blueprint.hive', apiary=apiary_selected))
        if db.session.query(HiveModel.hive_id).filter_by(apiary_id=hive.apiary_id,
                                                         hive_description=hive_description).scalar() is not None:
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
    id_hive_to_remove = request.args['to_remove']
    apiary = request.args['apiary']
    hive_to_remove = HiveModel.query.filter_by(hive_id=id_hive_to_remove).first()
    db.session.delete(hive_to_remove)
    db.session.query(SensorFeed).filter(SensorFeed.hive_id == id_hive_to_remove).update({'hive_id': ''})
    db.session.commit()
    return redirect(url_for('home_blueprint.hive', apiary=apiary))


@blueprint.route('/addSupers', methods=['GET'])
@login_required
def addSupers():
    hive_id = request.args['hive_id']
    apiary = request.args['apiary']
    data_to_modify = HiveModel.query.filter_by(hive_id=hive_id).first()
    data_to_modify.n_supers = data_to_modify.n_supers + 1
    db.session.commit()

    return redirect(url_for('home_blueprint.dashboard', apiary=apiary, hive_id=hive_id, type="none"))


@blueprint.route('/removeSupers', methods=['GET'])
@login_required
def removeSupers():
    hive_id = request.args['hive_id']
    apiary = request.args['apiary']
    data_to_modify = HiveModel.query.filter_by(hive_id=hive_id).first()
    data_to_modify.n_supers = data_to_modify.n_supers - 1
    if (data_to_modify.n_supers < 0):
        flash("There are no supers to remove.")
        return redirect(url_for('home_blueprint.dashboard', apiary=apiary, hive_id=hive_id, type="none"))
    db.session.commit()
    return redirect(url_for('home_blueprint.dashboard', apiary=apiary, hive_id=hive_id, type="none"))


# ----------------- SENSOR FEED AND DASHBOARD CONTROLLER ----------------- #


@blueprint.route('/sensorFeed', methods=['POST', 'GET'])
@login_required
def sensorFeed():
    hive_id = request.args["hive_id"]
    apiary_id = HiveModel.query.filter_by(hive_id=hive_id).first().apiary_id
    desc = HiveModel.query.filter_by(hive_id=hive_id).first().hive_description
    sf = SensorFeed.query.filter_by(hive_id=hive_id).all()

    return render_template('sensor-feed.html', sf=sf, apiary=apiary_id, hive=desc)


@blueprint.route('/dashboard', methods=['POST', 'GET'])
@login_required
def dashboard():
    hive_id = request.args["hive_id"]
    apiary = request.args["apiary"]

    sf = SensorFeed.query.filter_by(hive_id=hive_id)[-2000:]
    loc = ApiaryModel.query.filter_by(apiary_id=apiary).first().location
    hive = HiveModel.query.filter_by(hive_id=hive_id).first()
    entrance = hive.entrance
    alarm = hive.alarm
    w = weather(loc)

    swarmings = SwarmEvent.query.filter_by(hive_id=hive_id).all()
    swarmings_communications = SwarmCommunication.query.filter_by(hive_id=hive_id).all()

    one_week_ago = datetime.now() - timedelta(days=7)
    two_weeks_ago = datetime.now() - timedelta(days=14)
    today = SensorFeed.query.filter(SensorFeed.timestamp.startswith(datetime.now().strftime("%Y-%m-%d")),
                                    SensorFeed.hive_id == hive_id).order_by(SensorFeed.timestamp.desc()).first()
    this_week = SensorFeed.query.filter(SensorFeed.timestamp.between(one_week_ago, datetime.now()),
                                        SensorFeed.hive_id == hive_id).first()
    last_week = SensorFeed.query.filter(SensorFeed.timestamp.between(two_weeks_ago, one_week_ago),
                                        SensorFeed.hive_id == hive_id).first()

    if this_week is not None and today is not None:
        this_week_variation = today.weight - this_week.weight
    else:
        this_week_variation = "tbd"
    if this_week is not None and last_week is not None:
        last_week_variation = this_week.weight - last_week.weight
    else:
        last_week_variation = "tbd"

    try:
        next_week = honeyProductionPrediction(hive_id)
    except:
        next_week = "tdb"

    try:
        honey_prod = (sf[-1].weight * 100) / ((hive.n_supers * 30000) + 50000)
        min = (datetime.now() - sf[-1].timestamp).total_seconds() / 60.0
    except:
        flash("There are no data belonging to this specific hive.")
        return redirect(url_for('home_blueprint.hive', hive_id=hive_id, apiary=apiary))
    if min > 2 * hive.update_freq:
        time = False
    else:
        time = True

    dashboard = {"hive": hive, "apiary": apiary, "time": time, "sf": sf, "loc": loc, "w": w, "hp": int(honey_prod),
                 "swarm": swarmings, 'swarmings': swarmings, 'swarmings_communications': swarmings_communications,
                 "this_week": this_week_variation, "last_week": last_week_variation, "next_week": next_week}

    if request.args["type"] == "alarm":
        alarm = not alarm
        db.session.query(HiveModel).filter(HiveModel.hive_id == hive_id).update({'alarm': alarm})
        db.session.commit()
    if request.args["type"] == "entrance":
        entrance = not entrance
        db.session.query(HiveModel).filter(HiveModel.hive_id == hive_id).update({'entrance': entrance})
        db.session.commit()

    return render_template('dashboard.html', d=dashboard, type="none")


# ----------------- SWARMING EVENTS ----------------- #

@blueprint.route('/swarming', methods=['POST', 'GET'])
@login_required
def swarming():
    swarmings = db.session.query(SwarmEvent).join(HiveModel).join(ApiaryModel).join(User).filter(
        current_user.id == User.id).all()
    swarmings_communications = db.session.query(SwarmCommunication).join(HiveModel).join(ApiaryModel).join(User).filter(
        User.id == current_user.id).all()

    hives = db.session.query(HiveModel).join(ApiaryModel).join(User).filter(User.id == current_user.id).all()
    ids = []
    for el in hives:
        ids.append(el.hive_description)
    swarming_form = CreateSwarmEventForm(request.form)
    swarming_form.id_hive.choices = ids

    if 'new_swarming_event' in request.form:

        # read form data
        hive_description = request.form['id_hive']
        hive_id = HiveModel.query.filter_by(hive_description=hive_description).first().hive_id
        alert_date = request.form['alert_date']
        alert_begin = datetime.strptime(alert_date + ' ' + request.form['alert_start_time'], "%Y-%m-%d %H:%M")
        alert_end = datetime.strptime(alert_date + ' ' + request.form['alert_end_time'], "%Y-%m-%d %H:%M")
        t_var = request.form['temperature_variation']
        w_var = request.form['weight_variation']
        swarm_event = SwarmEvent(hive_id=hive_id, alert_period_begin=alert_begin, alert_period_end=alert_end,
                                 temperature_variation=t_var, weight_variation=w_var, real=True)

        try:
            db.session.add(swarm_event)
            db.session.commit()
        except Exception as e:
            print(e)
            flash("Impossible to add the swarming event!")
            return redirect(url_for('home_blueprint.swarming'))

        return redirect(url_for('home_blueprint.swarming'))

    if not current_user.is_authenticated:
        return render_template('swarming.html', form=swarming_form, swarmings=swarmings,
                               swarmings_communications=swarmings_communications)
    return render_template('swarming.html', form=swarming_form, swarmings=swarmings,
                           swarmings_communications=swarmings_communications)


@blueprint.route('/swarmingUpdate', methods=['GET'])
@login_required
def swarmingUpdate():
    swarm_id = request.args["swarm"]
    swarm = SwarmEvent.query.filter_by(swarm_id=swarm_id).first()
    db.session.query(SwarmEvent).filter(SwarmEvent.swarm_id == swarm.swarm_id).update({'real': not swarm.real})
    db.session.commit()

    return redirect(url_for('home_blueprint.swarming'))


@blueprint.route('/swarmingDelete', methods=['GET'])
@login_required
def swarmingDelete():
    swarm_id = request.args["swarm"]
    swarm = SwarmEvent.query.filter_by(swarm_id=swarm_id).first()
    db.session.delete(swarm)
    db.session.commit()

    return redirect(url_for('home_blueprint.swarming'))
