from app import app
from flask import *
from flask_user import *
from flask_login import login_user, logout_user
from app.models import *
import flask_menu as menu
from flask.ext import markdown
from sqlalchemy import func
from werkzeug.contrib.cache import SimpleCache
from urllib.parse import urlparse
cache = SimpleCache()

@app.template_filter()
def domain(url):
	return urlparse(url).netloc

# Use nginx to serve files on production instead
@app.route("/static/<path:path>")
def send_static(path):
	return send_from_directory("static", path)

@app.route("/uploads/<path:path>")
def send_upload(path):
	import os
	return send_from_directory(os.path.abspath(app.config["UPLOAD_FOLDER"]), path)

@app.route("/")
@menu.register_menu(app, ".", "Home")
def home_page():
	return render_template("index.html")

from . import users, githublogin, packages
