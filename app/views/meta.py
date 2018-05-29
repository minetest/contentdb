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
from app import app
from app.models import *

@app.route("/metapackages/")
def meta_package_list_page():
	mpackages = MetaPackage.query.order_by(db.asc(MetaPackage.name)).all()
	return render_template("meta/list.html", mpackages=mpackages)

@app.route("/metapackages/<name>/")
def meta_package_page(name):
	mpackage = MetaPackage.query.filter_by(name=name).first()
	if mpackage is None:
		abort(404)

	return render_template("meta/view.html", mpackage=mpackage)
