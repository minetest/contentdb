from app import app
from flask import *
from flask_user import *
from flask_login import login_user, logout_user
from app.models import *
import flask_menu as menu
from flask.ext import markdown
from sqlalchemy import func
from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()

# TODO: remove on production!
@app.route('/static/<path:path>')
def send_static(path):
	return send_from_directory('static', path)

import users, githublogin

@app.route('/')
@menu.register_menu(app, '.', 'Home')
def home_page():
	return render_template('index.html')
