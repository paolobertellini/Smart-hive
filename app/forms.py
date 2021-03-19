# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import TextField, PasswordField, SelectField, DateField, FileField
from wtforms.validators import Email, DataRequired, Required


## login and registration

class LoginForm(FlaskForm):
    username = TextField('Username', id='username_login', validators=[DataRequired()])
    password = PasswordField('Password', id='pwd_login', validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    username = TextField('Username', id='username_create', validators=[DataRequired()])
    email = TextField('Email', id='email_create', validators=[DataRequired(), Email()])
    password = PasswordField('Password', id='pwd_create', validators=[DataRequired()])


class CreateApiaryForm(FlaskForm):
    id_apiary = TextField('Apiary id', id='apiary_id_create', validators=[DataRequired()])
    location = TextField('Location', id='location')


class CreateHiveForm(FlaskForm):
    id_hive = TextField('Hive id', id='hive_id_create', validators=[DataRequired()])
    id_apiary = SelectField('Apiary id', id='apiary_id_create', validators=[DataRequired()])
    hive_description = TextField('Hive description', id='hive_description_create', validators=[DataRequired()])
    n_supers = TextField('Number of supers', id='n_supers_input', validators=[DataRequired()])
    association_code = TextField('Association code', id='association_code_input', validators=[DataRequired()])
    file = FileField('file')


class CreateAlarmForm(FlaskForm):
    duration = TextField('Sound duration', id='alarm_duration')


class CreateSwarmEventForm(FlaskForm):
    __tablename__ = 'SwarmEvent'
    id_hive = SelectField('Hive id', id='hive_id_create', validators=[DataRequired()])
    alert_date = DateField('Swarming date', id='alert-date', format='%m/%d/%y', validators=[Required()])
    alert_start_time = TextField('Start time', id='alert-start-time', validators=[Required()])
    alert_end_time = TextField('End time', id='alert-end-time', validators=[Required()])
    temperature_variation = TextField('Temperature variation', id='temp_var_create')
    weight_variation = TextField('Weight variation', id='temp_var_create')
