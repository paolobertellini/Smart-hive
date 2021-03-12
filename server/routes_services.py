from flask import request

from app import blueprint
from database.models import ApiaryModel, HiveModel, SensorFeed
from server import db

from swarmDetection import swarmDetection
from utility import weather

@blueprint.route('/autentication', methods=['GET'])
def autentication():
    req = request.get_json(force=True)
    hive_id = db.session.query(HiveModel.hive_id).filter_by(association_code=req['association_code']).scalar()
    return {'hive_id':hive_id}


@blueprint.route('/bridge-channel', methods=['GET', 'POST'])
def hiveState():
    req = request.get_json(force=True)
    hive_id = req['id']
    entrance = HiveModel.query.filter_by(hive_id=hive_id).first().entrance
    alarm = HiveModel.query.filter_by(hive_id=hive_id).first().alarm
    update_freq = HiveModel.query.filter_by(hive_id=hive_id).first().update_freq
    return ({'entrance': entrance, 'alarm': alarm, 'update_freq':update_freq})


@blueprint.route('/new-sensor-feed', methods=['GET', 'POST'])
# @login_required
def newSensorFeed():
    req = request.get_json(force=True)
    hive_id = req['hive_id']

    user_id = HiveModel.query.filter_by(hive_id=hive_id).first().user_id
    apiary_id = HiveModel.query.filter_by(hive_id=hive_id).first().apiary_id
    loc = ApiaryModel.query.filter_by(apiaty_id=apiary_id).first().location

    sensorFeed = SensorFeed(hive_id=req['hive_id'],
                            temperature=req['temperature'],
                            humidity=req['humidity'],
                            weight=req['weight'],
                            ext_temperature=weather(loc)['temperature']['temp'])

    db.session.add(sensorFeed)
    db.session.commit()

    swarmDetection(hive_id)

    return {'resp':200}
