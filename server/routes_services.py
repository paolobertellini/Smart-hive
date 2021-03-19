from datetime import datetime

from flask import request

from app import blueprint
from database.models import ApiaryModel, HiveModel, SensorFeed
from server import db
from utility.swarmDetection import swarmDetection
from utility.weather import weather


@blueprint.route('/authentication', methods=['GET'])
def authentication():
    req = request.get_json(force=True)
    hive_id = db.session.query(HiveModel.hive_id).filter_by(association_code=req['association_code']).scalar()
    return str(hive_id)


@blueprint.route('/bridge-channel', methods=['GET', 'POST'])
def hiveState():
    req = request.get_json(force=True)
    hive_id = req['id']
    entrance = HiveModel.query.filter_by(hive_id=hive_id).first().entrance
    alarm = HiveModel.query.filter_by(hive_id=hive_id).first().alarm
    update_freq = HiveModel.query.filter_by(hive_id=hive_id).first().update_freq
    return ({'entrance': entrance, 'alarm': alarm, 'update_freq': update_freq})


@blueprint.route('/new-sensor-feed', methods=['GET', 'POST'])
# @login_required
def newSensorFeed():
    req = request.get_json(force=True)

    apiary_id = HiveModel.query.filter_by(hive_id=req['hive_id']).first().apiary_id
    loc = ApiaryModel.query.filter_by(apiary_id=apiary_id).first().location

    w = weather(loc)

    sensorFeed = SensorFeed(hive_id=req['hive_id'],
                            temperature=req['temperature'],
                            humidity=req['humidity'],
                            weight=req['weight'],
                            ext_temperature=w['temperature'],
                            ext_humidity=w['humidity'],
                            wind=w['wind'],
                            timestamp=datetime.now())

    db.session.add(sensorFeed)
    db.session.commit()

    swarmDetection(req['hive_id'])

    return "200"
