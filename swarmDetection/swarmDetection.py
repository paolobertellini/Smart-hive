
from database.models import HiveModel, SensorFeed

from server import db

from datetime import datetime


#thresholds
int_ext_t = 3


def alertHives(hive):

    hives = HiveModel.query.filter_by(apiary_id=hive.apiary_id, entrance=False).all()
    for hive in hives:
        db.session.query(HiveModel).filter(HiveModel.hive_id == hive.hive_id).update({'entrance': True})
        db.session.commit()
        db.session.query(HiveModel).filter(HiveModel.hive_id == hive.hive_id).update({'sound': True})
        db.session.commit()

def swarmDetection(hive_id):
    hive = HiveModel.query.filter_by(hive_id=hive_id).first()
    sf = SensorFeed.query.filter_by(hive_id=hive_id).all()

    now = sf[-1]
    before = sf[-2]

    #           interna         -2                        esterna    +2
    delta = (now.temperature - before.temperature) - (now.ext_temperature - before.ext_temperature)
    if delta >= 1: # solo la temperatura interna sta aumentando
        if hive.update_freq == 1200:
            # salvo il timestamp di inizio allerta
            db.session.query(HiveModel).filter(HiveModel.hive_id == hive_id).update({'alert_period_begin': now.timestamp})
            db.session.commit()
            # incremento la frequenza di campionamento
            db.session.query(HiveModel).filter(HiveModel.hive_id == hive_id).update({'update_freq': 30})
            db.session.commit()
        
    if now.temperature < before.temperature: # la temperatura interna sta diminuendo

        db.session.query(HiveModel).filter(HiveModel.hive_id == hive_id).update({'update_freq': 120})
        db.session.commit()
        duration = (hive.alert_period_begin - now.timestamp).total_seconds() / 60.0
        if 7 < duration < 25:
            print("swarm detected")
            print(duration)
            alertHives(hive)
            return True
        else:
            print("false positive")

    return False


