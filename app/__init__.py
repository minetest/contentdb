from flask import *
from flask_user import *
import flask_menu as menu
from flask_mail import Mail
from flask.ext import markdown
from flask_github import GitHub
from flask_wtf.csrf import CsrfProtect
from flask_flatpages import FlatPages
import os

app = Flask(__name__)
app.config["FLATPAGES_ROOT"] = "flatpages"
app.config["FLATPAGES_EXTENSION"] = ".md"
app.config.from_pyfile(os.environ["FLASK_CONFIG"])

menu.Menu(app=app)
markdown.Markdown(app, extensions=["fenced_code"], safe_mode=True, output_format="html5")
github = GitHub(app)
csrf = CsrfProtect(app)
mail = Mail(app)
pages = FlatPages(app)

from . import models, tasks
from .views import *
