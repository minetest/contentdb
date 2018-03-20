from flask import *
from flask_user import *
import flask_menu as menu
from flask.ext import markdown
from flask_github import GitHub

app = Flask(__name__)
app.config.from_pyfile('../config.cfg')

menu.Menu(app=app)
markdown.Markdown(app, extensions=['fenced_code'])
github = GitHub(app)

from . import models
from .views import *
