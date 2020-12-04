# ContentDB
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
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *

from app.models import *
from app.utils import rank_required
from . import bp


@bp.route("/licenses/")
@rank_required(UserRank.MODERATOR)
def license_list():
	return render_template("admin/licenses/list.html", licenses=License.query.order_by(db.asc(License.name)).all())

class LicenseForm(FlaskForm):
	name	 = StringField("Name", [InputRequired(), Length(3,100)])
	is_foss  = BooleanField("Is FOSS")
	submit   = SubmitField("Save")

@bp.route("/licenses/new/", methods=["GET", "POST"])
@bp.route("/licenses/<name>/edit/", methods=["GET", "POST"])
@rank_required(UserRank.MODERATOR)
def create_edit_license(name=None):
	license = None
	if name is not None:
		license = License.query.filter_by(name=name).first()
		if license is None:
			abort(404)

	form = LicenseForm(formdata=request.form, obj=license)
	if request.method == "GET" and license is None:
		form.is_foss.data = True
	elif request.method == "POST" and form.validate():
		if license is None:
			license = License(form.name.data)
			db.session.add(license)
			flash("Created license " + form.name.data, "success")
		else:
			flash("Updated license " + form.name.data, "success")

		form.populate_obj(license)
		db.session.commit()
		return redirect(url_for("admin.license_list"))

	return render_template("admin/licenses/edit.html", license=license, form=form)
