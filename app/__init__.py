from flask import *
from flask_user import *
import flask_menu as menu
from flask.ext import markdown
from flask_github import GitHub
from flask_wtf.csrf import CsrfProtect
import os



app = Flask(__name__)
app.config.from_pyfile(os.environ["FLASK_CONFIG"])

menu.Menu(app=app)
markdown.Markdown(app, extensions=["fenced_code"], safe_mode=True, output_format="html5")
github = GitHub(app)
csrf = CsrfProtect(app)

from . import models, tasks
from .views import *
