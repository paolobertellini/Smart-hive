# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import atexit
from sys import exit

from apscheduler.schedulers.background import BackgroundScheduler
from decouple import config
from flask_migrate import Migrate

from AI.dataPrediction import honeyProductionFit
from config import config_dict
from server import create_app, db

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

scheduler = BackgroundScheduler()
scheduler.add_job(func=honeyProductionFit, trigger="interval", seconds=20)  # hours=1
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if DEBUG:
    app.logger.info('DEBUG       = ' + str(DEBUG))
    app.logger.info('Environment = ' + get_config_mode)
    app.logger.info('DBMS        = ' + app_config.SQLALCHEMY_DATABASE_URI)

if __name__ == "__main__":
    app.run(host=app.config.get('FLASK_RUN_HOST'), port=app.config.get('FLASK_RUN_PORT'))
