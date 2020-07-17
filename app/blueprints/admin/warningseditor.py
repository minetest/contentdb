# ContentDB
# Copyright (C) 2020  rubenwardy
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
from . import bp
from app.models import *
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from app.utils import rank_required

@bp.route("/admin/warnings/")
@rank_required(UserRank.ADMIN)
def warning_list():
	return render_template("admin/warnings/list.html", warnings=ContentWarning.query.order_by(db.asc(ContentWarning.title)).all())

class WarningForm(FlaskForm):
	title	    = StringField("Title", [InputRequired(), Length(3,100)])
	name        = StringField("Name", [Optional(), Length(1, 20), Regexp("^[a-z0-9_]", 0, "Lower case letters (a-z), digits (0-9), and underscores (_) only")])
	description = TextAreaField("Description", [InputRequired(), Length(0, 500)])
	submit      = SubmitField("Save")

@bp.route("/admin/warnings/new/", methods=["GET", "POST"])
@bp.route("/admin/warnings/<name>/edit/", methods=["GET", "POST"])
@rank_required(UserRank.ADMIN)
def create_edit_warning(name=None):
	warning = None
	if name is not None:
		warning = ContentWarning.query.filter_by(name=name).first()
		if warning is None:
			abort(404)

	form = WarningForm(formdata=request.form, obj=warning)
	if request.method == "POST" and form.validate():
		if warning is None:
			warning = ContentWarning(form.title.data, form.description.data)
			db.session.add(warning)
		else:
			form.populate_obj(warning)
		db.session.commit()

		return redirect(url_for("admin.warning_list"))

	return render_template("admin/warnings/edit.html", warning=warning, form=form)
