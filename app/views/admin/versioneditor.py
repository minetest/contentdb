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
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from app.utils import rank_required

@app.route("/versions/")
@rank_required(UserRank.MODERATOR)
def version_list_page():
	return render_template("admin/versions/list.html", versions=MinetestRelease.query.order_by(db.asc(MinetestRelease.id)).all())

class VersionForm(FlaskForm):
	name	 = StringField("Name", [InputRequired(), Length(3,100)])
	protocol = IntegerField("Protocol")
	submit   = SubmitField("Save")

@app.route("/versions/new/", methods=["GET", "POST"])
@app.route("/versions/<name>/edit/", methods=["GET", "POST"])
@rank_required(UserRank.MODERATOR)
def createedit_version_page(name=None):
	version = None
	if name is not None:
		version = MinetestRelease.query.filter_by(name=name).first()
		if version is None:
			abort(404)

	form = VersionForm(formdata=request.form, obj=version)
	if request.method == "POST" and form.validate():
		if version is None:
			version = MinetestRelease(form.name.data)
			db.session.add(version)
			flash("Created version " + form.name.data, "success")
		else:
			flash("Updated version " + form.name.data, "success")

		form.populate_obj(version)
		db.session.commit()
		return redirect(url_for("version_list_page"))

	return render_template("admin/versions/edit.html", version=version, form=form)
