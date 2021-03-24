import os

import pandas as pd
import requests
from sqlalchemy import create_engine
import pickle
from sklearn import linear_model

#from config import model
from database.models import ApiaryModel, HiveModel

api_key = 'c984a283dfd9a79d06e234a7c62f2e2a'
basedir = os.path.abspath(os.path.dirname(__file__))
engine = create_engine('sqlite:///' + basedir + '/../database/db.sqlite3')
filename = 'finalized_model.sav'


def honeyProductionFit():
    print("Fitting..")

    df = pd.read_sql_table('SensorFeed', engine)
    df = df.dropna()

    df['month'] = pd.DatetimeIndex(df['timestamp']).month
    df['day'] = pd.DatetimeIndex(df['timestamp']).day
    df['hour'] = pd.DatetimeIndex(df['timestamp']).hour
    df['minute'] = pd.DatetimeIndex(df['timestamp']).minute

    for index in range(len(df)):
        if index == 0:
            df['weight_deviation'] = 0
        else:
            if df['timestamp'][index].year != df['timestamp'][index - 1].year:
                df.loc[index, 'weight_deviation'] = 0
            else:
                df.loc[index, 'weight_deviation'] = df.loc[index, 'weight'] - df.loc[index - 1, 'weight']

    X = df[['ext_humidity', 'ext_temperature', 'wind', 'month', 'day', 'hour', 'minute']]
    Y = df['weight_deviation']

    # train_lenght = int(len(df) * 80 / 100)
    # X_train = X[:-train_lenght]
    # Y_train = Y[:-train_lenght]
    # X_test = X[-train_lenght:]
    # Y_test = Y[-train_lenght:]

    model = linear_model.LinearRegression()
    model.fit(X, Y)
    pickle.dump(model, open(filename, 'wb'))
    print("Fitting completed")


def honeyProductionPrediction(hive_id):
    apiary = HiveModel.query.filter_by(hive_id=hive_id).first().apiary_id
    city = ApiaryModel.query.filter_by(apiary_id=apiary).first().location

    forecast = pd.DataFrame(columns=['ext_humidity', 'ext_temperature', 'wind', 'month', 'day', 'hour', 'minute'])
    api_call = 'https://api.openweathermap.org/data/2.5/forecast?appid=' + api_key
    api_call += '&q=' + city
    json_data = requests.get(api_call).json()
    current_date = ''
    for item in json_data['list']:
        time = item['dt_txt']
        next_date, hour1 = time.split(' ')
        if current_date != next_date:
            current_date = next_date
            year, month, day = current_date.split('-')

        temperature = item['main']['temp'] - 273.15
        # description = item['weather'][0]['description'],
        humidity = item['main']['humidity']
        wind = item['wind']['speed']

        # mytime = dt.datetime.strptime(str(current_date) + ' ' + str(hour1), '%Y-%m-%d %H:%M:%S')
        # Prints the description as well as the temperature in Celcius and Farenheit
        forecast = forecast.append(
            {'ext_humidity': humidity, 'ext_temperature': temperature, 'wind': wind, 'month': month, 'day': day,
             'hour': hour1[:2], 'minute': hour1[3:5]}, ignore_index=True)

    loaded_model = pickle.load(open(filename, 'rb'))
    Y_pred = loaded_model.predict(forecast)
    # print(Y_pred)
    return Y_pred.sum()

honeyProductionFit()