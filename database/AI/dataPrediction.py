from sqlalchemy import create_engine
import os
import requests
import datetime as dt
from sklearn import datasets, linear_model
from database.models import  SensorFeed, ApiaryModel,HiveModel
import pandas as pd
api_key = 'c984a283dfd9a79d06e234a7c62f2e2a'
basedir = os.path.abspath(os.path.dirname(__file__))
engine = create_engine('sqlite:///'+basedir+'/../db.sqlite3')


def honeyProductionFit(hive_id):
    df = pd.DataFrame()
    data=pd.read_sql_table('SensorFeed',engine)
    apiary = HiveModel.query.filter_by(hive_id=hive_id).first().apiary_id
    hives = HiveModel.query.filter_by(apiary_id=apiary).all()
    for hive in hives:
        df=df.append(data[data["hive_id"]==str(hive.hive_id)],ignore_index = True)

    df=df.dropna()
    df['month'] = pd.DatetimeIndex(df['timestamp']).month
    df['day'] = pd.DatetimeIndex(df['timestamp']).day
    df['hour'] = pd.DatetimeIndex(df['timestamp']).hour
    df['minute'] = pd.DatetimeIndex(df['timestamp']).minute
    for index in range(len(df)):
        if index==0:
            df['weight_deviation']=0
        else:
            if(df['timestamp'][index].year!=df['timestamp'][index-1].year):
                df['weight_deviation'][index]=0
            else:
                df['weight_deviation'][index]=df['weight'][index]-df['weight'][index-1]
    X = df[['ext_humidity','ext_temperature','wind','month','day','hour','minute']]
    Y = df['weight_deviation']
    train_lenght= int(len(df)*80/100)
    X_train = X[:-train_lenght]
    Y_train = Y[:-train_lenght]
    X_test = X[-train_lenght:]
    Y_test = Y[-train_lenght:]
    regr = linear_model.LinearRegression()
    regr.fit(X_train, Y_train)
    return(regr)

def honeyProductionPrediction(regr,hive_id):
    apiary = HiveModel.query.filter_by(hive_id=hive_id).first().apiary_id
    city = ApiaryModel.query.filter_by(apiary_id=apiary).first().location
    forecast = pd.DataFrame (columns = ['ext_humidity','ext_temperature' ,'wind','month','day','hour','minute'])
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

        temperature = item['main']['temp']-273.15
        description = item['weather'][0]['description'],
        humidity = item['main']['humidity']
        wind = item['wind']['speed']

        mytime = dt.datetime.strptime(str(current_date)+' '+str(hour1),'%Y-%m-%d %H:%M:%S')
        # Prints the description as well as the temperature in Celcius and Farenheit
        forecast=forecast.append({'ext_humidity':humidity,'ext_temperature':temperature ,'wind':wind,'month':month,'day':day,'hour':hour1[:2],'minute':hour1[3:5]},ignore_index=True)

    Y_pred = regr.predict(forecast)
    print(Y_pred)


