# ContentDB
# Copyright (C) 2018-21 rubenwardy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from flask import redirect, render_template, abort, url_for, request, flash
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, URLField
from wtforms.validators import InputRequired, Length, Optional

from app.utils import rank_required, nonempty_or_none, add_audit_log
from . import bp
from app.models import UserRank, License, db, AuditSeverity


@bp.route("/licenses/")
@rank_required(UserRank.MODERATOR)
def license_list():
	return render_template("admin/licenses/list.html", licenses=License.query.order_by(db.asc(License.name)).all())


class LicenseForm(FlaskForm):
	name = StringField("Name", [InputRequired(), Length(3, 100)])
	is_foss = BooleanField("Is FOSS")
	url = URLField("URL", [Optional()], filters=[nonempty_or_none])
	submit = SubmitField("Save")


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
	elif form.validate_on_submit():
		if license is None:
			license = License(form.name.data)
			db.session.add(license)
			flash("Created license " + form.name.data, "success")

			add_audit_log(AuditSeverity.MODERATION, current_user, f"Created license {license.name}",
						  url_for("admin.license_list"))
		else:
			flash("Updated license " + form.name.data, "success")

			add_audit_log(AuditSeverity.MODERATION, current_user, f"Edited license {license.name}",
						  url_for("admin.license_list"))

		form.populate_obj(license)
		db.session.commit()
		return redirect(url_for("admin.license_list"))

	return render_template("admin/licenses/edit.html", license=license, form=form)
