# ContentDB
# Copyright (C) 2018-24 rubenwardy
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


from flask import redirect, render_template, abort, url_for
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import InputRequired, Length, Optional

from app.models import db, AuditSeverity, UserRank, Language
from app.utils import add_audit_log, rank_required
from . import bp


@bp.route("/admin/languages/")
@rank_required(UserRank.ADMIN)
def language_list():
	return render_template("admin/languages/list.html", languages=Language.query.all())


class LanguageForm(FlaskForm):
	id = StringField("Id", [InputRequired(), Length(2, 10)])
	title = TextAreaField("Title", [Optional(), Length(2, 100)])
	submit = SubmitField("Save")


@bp.route("/admin/languages/new/", methods=["GET", "POST"])
@bp.route("/admin/languages/<id_>/edit/", methods=["GET", "POST"])
@rank_required(UserRank.ADMIN)
def create_edit_language(id_=None):
	language = None
	if id_ is not None:
		language = Language.query.filter_by(id=id_).first()
		if language is None:
			abort(404)

	form = LanguageForm(obj=language)
	if form.validate_on_submit():
		if language is None:
			language = Language()
			db.session.add(language)
			form.populate_obj(language)

			add_audit_log(AuditSeverity.EDITOR, current_user, f"Created language {language.id}",
					url_for("admin.create_edit_language", id_=language.id))
		else:
			form.populate_obj(language)

			add_audit_log(AuditSeverity.EDITOR, current_user, f"Edited language {language.id}",
					url_for("admin.create_edit_language", id_=language.id))

		db.session.commit()
		return redirect(url_for("admin.create_edit_language", id_=language.id))

	return render_template("admin/languages/edit.html", language=language, form=form)
