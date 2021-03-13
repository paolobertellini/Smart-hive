
from database.models import HiveModel, SensorFeed, SwarmEvent

from server import db

from datetime import datetime



std_interval = 60
alert_interval = 10

def alertHives(hive):

    hives = HiveModel.query.filter_by(apiary_id=hive.apiary_id, entrance=False).all()
    for hive in hives:
        db.session.query(HiveModel).filter(HiveModel.hive_id == hive.hive_id).update({'entrance': True})
        db.session.query(HiveModel).filter(HiveModel.hive_id == hive.hive_id).update({'alarm': True})
        db.session.commit()

def swarmDetection(hive_id):
    hive = HiveModel.query.filter_by(hive_id=hive_id).first()
    sf = SensorFeed.query.filter_by(hive_id=hive_id).all()

    if len(sf) >= 2:

        now = sf[-1]
        before = sf[-2]
        #           interna         -2                        esterna    +2
        delta = (now.temperature - before.temperature) - (now.ext_temperature - before.ext_temperature)

        # swarming start
        if delta >= 1:
            if hive.update_freq == std_interval:
                swarm_event = SwarmEvent(user_id=hive.user_id, hive_id=hive_id,
                                         alert_period_begin=now.timestamp, alert_period_end=None,
                                         temperature_variation=now.temperature, weight_variation=now.weight, real=False)
                db.session.add(swarm_event)
                # db.session.query(HiveModel).filter(HiveModel.hive_id == hive_id).update({'alert_period_begin': now.timestamp})
                db.session.query(HiveModel).filter(HiveModel.hive_id == hive_id).update({'update_freq': alert_interval})
                db.session.commit()
                alertHives(hive)
                print("Alert period started")

        # swarming end
        if now.temperature < before.temperature and hive.update_freq != std_interval: # la temperatura interna sta diminuendo
            swarm_events = SwarmEvent.query.filter_by(hive_id=hive_id).all()
            swarm_event_id=swarm_events[-1].swarm_id
            db.session.query(SwarmEvent).filter(SwarmEvent.swarm_id == swarm_event_id).update({'alert_period_end': now.timestamp})
            old_temperature = swarm_events[-1].temperature_variation
            db.session.query(SwarmEvent).filter(SwarmEvent.swarm_id == swarm_event_id).update({'temperature_variation': old_temperature - now.temperature})
            old_weight = swarm_events[-1].weight_variation
            db.session.query(SwarmEvent).filter(SwarmEvent.swarm_id == swarm_event_id).update({'weight_variation': now.weight - old_weight})
            alert_period_begin = swarm_events[-1].alert_period_begin
            duration = (now.timestamp - alert_period_begin).total_seconds() #/ 60.0

            print(duration)
            if 25 < duration < 100 and now.weight - old_weight < 0:
                print("swarm detected")
                db.session.query(SwarmEvent).filter(SwarmEvent.swarm_id == swarm_event_id).update({'real': True})

            else:
                db.session.query(SwarmEvent).filter(SwarmEvent.swarm_id == swarm_event_id).update({'real': False})
                print("false positive")

            db.session.query(HiveModel).filter(HiveModel.hive_id == hive_id).update({'update_freq': std_interval})
            db.session.commit()
            print("Alert period ended")

    return False


