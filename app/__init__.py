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
from flask_github import GitHub
from flask_wtf.csrf import CsrfProtect
from flask_flatpages import FlatPages
from flask_babel import Babel
import os, redis

app = Flask(__name__, static_folder="public/static")
app.config["FLATPAGES_ROOT"] = "flatpages"
app.config["FLATPAGES_EXTENSION"] = ".md"
app.config.from_pyfile(os.environ["FLASK_CONFIG"])

r = redis.Redis.from_url(app.config["REDIS_URL"])

menu.Menu(app=app)
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

from .sass import sass
sass(app)


if not app.debug and app.config["MAIL_UTILS_ERROR_SEND_TO"]:
	from .maillogger import register_mail_error_handler
	register_mail_error_handler(app, mail)


from .markdown import init_app
init_app(app)


@babel.localeselector
def get_locale():
	return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

from . import models, tasks, template_filters

from .blueprints import create_blueprints
create_blueprints(app)

from flask_login import logout_user

@app.route("/uploads/<path:path>")
def send_upload(path):
	return send_from_directory(app.config['UPLOAD_DIR'], path)

@menu.register_menu(app, ".help", "Help", order=19, endpoint_arguments_constructor=lambda: { 'path': 'help' })
@app.route('/<path:path>/')
def flatpage(path):
    page = pages.get_or_404(path)
    template = page.meta.get('template', 'flatpage.html')
    return render_template(template, page=page)

@app.before_request
def check_for_ban():
	if current_user.is_authenticated:
		if current_user.rank == models.UserRank.BANNED:
			flash("You have been banned.", "error")
			logout_user()
			return redirect(url_for('user.login'))
		elif current_user.rank == models.UserRank.NOT_JOINED:
			current_user.rank = models.UserRank.MEMBER
			models.db.session.commit()
