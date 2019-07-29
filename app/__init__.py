# Content DB
# Copyright (C) 2018  rubenwardy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from flask import *
from flask_user import *
from flask_gravatar import Gravatar
import flask_menu as menu
from flask_mail import Mail
from flaskext.markdown import Markdown
from flask_github import GitHub
from flask_wtf.csrf import CsrfProtect
from flask_flatpages import FlatPages
from flask_babel import Babel
import os

app = Flask(__name__, static_folder="public/static")
app.config["FLATPAGES_ROOT"] = "flatpages"
app.config["FLATPAGES_EXTENSION"] = ".md"
app.config.from_pyfile(os.environ["FLASK_CONFIG"])

menu.Menu(app=app)
markdown = Markdown(app, extensions=["fenced_code"], safe_mode=True, output_format="html5")
github = GitHub(app)
csrf = CsrfProtect(app)
mail = Mail(app)
pages = FlatPages(app)
babel = Babel(app)
gravatar = Gravatar(app,
		size=58,
		rating='g',
		default='mp',
		force_default=False,
		force_lower=False,
		use_ssl=True,
		base_url=None)

if not app.debug:
	from .maillogger import register_mail_error_handler
	register_mail_error_handler(app, mail)


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys())


from . import models, tasks
from .views import *
