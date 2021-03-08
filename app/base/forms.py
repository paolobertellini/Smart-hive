# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import TextField, PasswordField
from wtforms.validators import InputRequired, Email, DataRequired

## login and registration

class LoginForm(FlaskForm):
    username = TextField    ('Username', id='username_login'   , validators=[DataRequired()])
    password = PasswordField('Password', id='pwd_login'        , validators=[DataRequired()])

class CreateAccountForm(FlaskForm):
    username = TextField('Username'     , id='username_create' , validators=[DataRequired()])
    email    = TextField('Email'        , id='email_create'    , validators=[DataRequired(), Email()])
    password = PasswordField('Password' , id='pwd_create'      , validators=[DataRequired()])

class CreateApiaryForm(FlaskForm):
    id_apiary = TextField('Apiary id'     , id='apiary_id_create'         , validators=[DataRequired()])
    location = TextField('Location', id='location')


class CreateHiveForm(FlaskForm):
    id_hive = TextField('Hive id', id='hive_id_create', validators=[DataRequired()])
    id_apiary = TextField('Apiary id', id='apiary_id_create', validators=[DataRequired()]) #forse non è necessario
    hive_description = TextField('Hive description', id='hive_description_create', validators=[DataRequired()])
    association_code = TextField('Association code', id='association_code_input', validators=[DataRequired()])

class CreateAlarmForm(FlaskForm):
    duration = TextField('Sound duration', id='alarm_duration')