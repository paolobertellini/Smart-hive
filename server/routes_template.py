# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template
from flask import request, redirect, url_for
from flask_login import (
    current_user,
    login_required
)
from jinja2 import TemplateNotFound

from app import blueprint
from database.models import ApiaryModel, HiveModel


@blueprint.app_context_processor
def inject_apiaries():
    if current_user.is_authenticated:
        apiaries = ApiaryModel.query.filter_by(user_id=current_user.id).all()
    else:
        apiaries = ""

    def find_hives(apiary):
        hives = HiveModel.query.filter_by(apiary_id=apiary).all()
        return hives

    return dict(apiaries=apiaries, find_hives=find_hives, type="none")


@blueprint.route('/')
def route_default():
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/index')
def index():
    return render_template('index.html', segment='index')


@blueprint.route('/<template>')
@login_required
def route_template(template):
    try:
        if not template.endswith('.html'):
            template += '.html'
        # Detect the current page
        segment = get_segment(request)
        # Serve the file (if exists) from app/templates/FILE.html
        return render_template(template, segment=segment)
    except TemplateNotFound:
        return render_template('errors/page-404.html'), 404
    except:
        return render_template('errors/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None
