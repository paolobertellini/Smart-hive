from database.models import HiveModel, SensorFeed, SwarmEvent, SwarmCommunication, User, ApiaryModel
from server import db
from config import sensorFeed_std_freq, sensorFeed_alert_freq
from utility.SmartHive_bot import sendMessage

std_interval = sensorFeed_std_freq
alert_interval = sensorFeed_alert_freq


def alertHives(hive):
    hives = HiveModel.query.filter_by(apiary_id=hive.apiary_id, entrance=False).all()
    for h in hives:
        db.session.query(HiveModel).filter(HiveModel.hive_id == h.hive_id).update({'entrance': True})
        db.session.query(HiveModel).filter(HiveModel.hive_id == h.hive_id).update({'alarm': True})

        swarm_id = SwarmEvent.query.filter_by(hive_id=hive.hive_id).order_by(
            SwarmEvent.swarm_id.desc()).first().swarm_id

        last_sf = SensorFeed.query.filter_by(hive_id=h.hive_id).order_by(SensorFeed.timestamp.desc()).first()
        swarm_communication = SwarmCommunication(hive_id=h.hive_id, swarm_id=swarm_id, weight_variation=last_sf.weight)

        db.session.add(swarm_communication)
        db.session.commit()

    user_id = ApiaryModel.query.filter_by(apiary_id=hive.apiary_id).first().user_id
    idTelegram = User.query.filter_by(id=user_id).first().idTelegram
    msg = "Attention! The hive with id " + str(hive.hive_id) + " is swarming just now!"
    sendMessage(msg=msg, chatID=idTelegram)


def alertEndHives(hive):
    swarm_id = SwarmEvent.query.filter_by(hive_id=hive.hive_id).order_by(
        SwarmEvent.swarm_id.desc()).first().swarm_id

    allarmed_hives = SwarmCommunication.query.filter_by(swarm_id=swarm_id).all()

    for hive in allarmed_hives:

        db.session.query(HiveModel).filter(HiveModel.hive_id == hive.hive_id).update({'alarm': False})

        weight_now = SensorFeed.query.filter_by(hive_id=hive.hive_id).order_by(
            SensorFeed.timestamp.desc()).first().weight
        weight_before = SwarmCommunication.query.filter_by(hive_id=hive.hive_id,
                                                           swarm_id=swarm_id).first().weight_variation

        # db.session.query(SwarmCommunication).filter(SwarmCommunication.hive_id == hive.hive_id,
        #                                             SwarmCommunication.swarm_id == swarm_id).update()

        if weight_now - weight_before < 500:
            db.session.query(HiveModel).filter(HiveModel.hive_id == hive.hive_id).update({'entrance': False})

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
        if delta >= 2:
            if hive.update_freq == std_interval:
                swarm_event = SwarmEvent(hive_id=hive_id,
                                         alert_period_begin=now.timestamp, alert_period_end=None,
                                         temperature_variation=now.temperature, weight_variation=now.weight, real=False)
                db.session.add(swarm_event)
                # db.session.query(HiveModel).filter(HiveModel.hive_id == hive_id).update({'alert_period_begin': now.timestamp})
                db.session.query(HiveModel).filter(HiveModel.hive_id == hive_id).update({'update_freq': alert_interval})
                db.session.commit()

                alertHives(hive)
                print("Alert period started")

        # swarming end
        swarm_event = SwarmEvent.query.filter_by(hive_id=hive_id, alert_period_end=None).order_by(SwarmEvent.swarm_id.desc()).first()
        if swarm_event:
            alert_period_begin = swarm_event.alert_period_begin
            duration = (now.timestamp - alert_period_begin).total_seconds() / 60.0
            if (now.temperature < before.temperature and hive.update_freq != std_interval) or duration > 30:  # la temperatura interna sta diminuendo
                db.session.query(SwarmEvent).filter(SwarmEvent.swarm_id == swarm_event.swarm_id).update(
                    {'alert_period_end': now.timestamp})
                old_temperature = swarm_event.temperature_variation
                db.session.query(SwarmEvent).filter(SwarmEvent.swarm_id == swarm_event.swarm_id).update(
                    {'temperature_variation': old_temperature - now.temperature})
                old_weight = swarm_event.weight_variation
                db.session.query(SwarmEvent).filter(SwarmEvent.swarm_id == swarm_event.swarm_id).update(
                    {'weight_variation': now.weight - old_weight})

                print(duration)
                if 8 < duration < 20 and now.weight - old_weight < 0:
                    print("swarm detected")
                    db.session.query(SwarmEvent).filter(SwarmEvent.swarm_id == swarm_event.swarm_id).update({'real': True})
                    user_id = ApiaryModel.query.filter_by(apiary_id=hive.apiary_id).first().user_id
                    idTelegram = User.query.filter_by(id=user_id).first().idTelegram
                    msg = "Attention! Please check the hive with id " + str(hive.hive_id) + " because there is a swarm!"
                    sendMessage(msg=msg, chatID=idTelegram)

                else:
                    db.session.query(SwarmEvent).filter(SwarmEvent.swarm_id == swarm_event.swarm_id).update({'real': False})

                    user_id = ApiaryModel.query.filter_by(apiary_id=hive.apiary_id).first().user_id
                    idTelegram = User.query.filter_by(id=user_id).first().idTelegram
                    msg = "False alarm! The hive with id" + str(hive.hive_id) + " is not swarming!"
                    sendMessage(msg=msg, chatID=idTelegram)

                    print("false positive")

                db.session.query(HiveModel).filter(HiveModel.hive_id == hive_id).update({'update_freq': std_interval})
                db.session.commit()
                alertEndHives(hive)
                print("Alert period ended")

    return False
