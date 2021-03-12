from flask import request

from app import blueprint
from database.models import HiveModel, SensorFeed
from server import db


@blueprint.route('/test', methods=['GET'])
def test():
    return "200"


@blueprint.route('/bridge-channel', methods=['GET', 'POST'])
def hiveState():
    req = request.get_json(force=True)
    hive_id = req['id']
    entrance = HiveModel.query.filter_by(hive_id=hive_id).first().entrance
    alarm = HiveModel.query.filter_by(hive_id=hive_id).first().alarm
    return ({'entrance': entrance, 'alarm': alarm})


@blueprint.route('/new-sensor-feed', methods=['GET', 'POST'])
# @login_required
def newSensorFeed():
    req = request.get_json(force=True)
    hive_id = db.session.query(HiveModel.hive_id).filter_by(association_code=req['association_code']).scalar()

    if (hive_id is not None):
        user_id = HiveModel.query.filter_by(hive_id=hive_id).first().user_id
        apiary_id = HiveModel.query.filter_by(hive_id=hive_id).first().apiary_id
        sensorFeed = SensorFeed(hive_id=req['hive_id'],
                                temperature=req['temperature'],
                                humidity=req['humidity'],
                                weight=req['weight'])
        if (str(hive_id) == req['hive_id']):
            db.session.add(sensorFeed)
            db.session.commit()
        return ({'hive_id': hive_id, 'user_id': user_id, 'apiary_id': apiary_id})
    else:
        return ({'hive_id': None, 'user_id': None, 'apiary_id': None})
