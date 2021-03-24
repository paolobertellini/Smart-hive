# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import atexit
from datetime import datetime
from sys import exit

from apscheduler.schedulers.background import BackgroundScheduler
from decouple import config
from flask_migrate import Migrate

from config import config_dict
from server import create_app, db
from utility.SmartHive_bot import botStart
from utility.checkStatus import checkStatus
from utility.dataPrediction import honeyProductionFit

# WARNING: Don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# The configuration
get_config_mode = 'Debug' if DEBUG else 'Production'

try:
    # Load the configuration using the default values 
    app_config = config_dict[get_config_mode.capitalize()]

except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

app = create_app(app_config)
Migrate(app, db)

schedulerCheckStatus = BackgroundScheduler()
schedulerCheckStatus.add_job(func=checkStatus, trigger="interval", max_instances=1, minutes=30,
                             next_run_time=datetime.now())
schedulerCheckStatus.start()
schedulerPrediction = BackgroundScheduler()
schedulerPrediction.add_job(func=honeyProductionFit, trigger="interval", hours=12, max_instances=1,
                            next_run_time=datetime.now())
schedulerPrediction.start()
schedulerBotTelegram = BackgroundScheduler()
schedulerBotTelegram.add_job(func=botStart)
schedulerBotTelegram.start()



# Shut down the scheduler when exiting the app
atexit.register(lambda: schedulerPrediction.shutdown())
atexit.register(lambda: schedulerCheckStatus.shutdown())
atexit.register(lambda: schedulerBotTelegram.shutdown())

if DEBUG:
    app.logger.info('DEBUG       = ' + str(DEBUG))
    app.logger.info('Environment = ' + get_config_mode)
    app.logger.info('DBMS        = ' + app_config.SQLALCHEMY_DATABASE_URI)

if __name__ == "__main__":
    app.run(host=app.config.get('FLASK_RUN_HOST'), port=app.config.get('FLASK_RUN_PORT'))
