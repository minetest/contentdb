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


from app import app, pages
from flask import *
from flask_user import *
from app.models import *
import flask_menu as menu
from werkzeug.contrib.cache import SimpleCache
from urllib.parse import urlparse
from sqlalchemy.sql.expression import func
cache = SimpleCache()

@app.template_filter()
def throw(err):
	raise Exception(err)

@app.template_filter()
def domain(url):
	return urlparse(url).netloc

@app.template_filter()
def date(value):
    return value.strftime("%Y-%m-%d")

@app.template_filter()
def datetime(value):
    return value.strftime("%Y-%m-%d %H:%M") + " UTC"

@app.route("/uploads/<path:path>")
def send_upload(path):
	return send_from_directory("public/uploads", path)

@app.route("/")
@menu.register_menu(app, ".", "Home")
def home_page():
	query   = Package.query.filter_by(approved=True, soft_deleted=False)
	count   = query.count()
	new     = query.order_by(db.desc(Package.created_at)).limit(8).all()
	pop_mod = query.filter_by(type=PackageType.MOD).order_by(db.desc(Package.score)).limit(8).all()
	pop_gam = query.filter_by(type=PackageType.GAME).order_by(db.desc(Package.score)).limit(4).all()
	pop_txp = query.filter_by(type=PackageType.TXP).order_by(db.desc(Package.score)).limit(4).all()
	downloads = db.session.query(func.sum(PackageRelease.downloads)).first()[0]
	return render_template("index.html", count=count, downloads=downloads, \
			new=new, pop_mod=pop_mod, pop_txp=pop_txp, pop_gam=pop_gam)

from . import users, packages, meta, threads, api
from . import sass, thumbnails, tasks, admin

@menu.register_menu(app, ".help", "Help", order=19, endpoint_arguments_constructor=lambda: { 'path': 'help' })
@app.route('/<path:path>/')
def flatpage(path):
    page = pages.get_or_404(path)
    template = page.meta.get('template', 'flatpage.html')
    return render_template(template, page=page)

@app.before_request
def do_something_whenever_a_request_comes_in():
	if current_user.is_authenticated:
		if current_user.rank == UserRank.BANNED:
			flash("You have been banned.", "error")
			logout_user()
			return redirect(url_for('user.login'))
		elif current_user.rank == UserRank.NOT_JOINED:
			current_user.rank = UserRank.MEMBER
			db.session.commit()
