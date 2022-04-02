# ContentDB
# Copyright (C) 2022 rubenwardy
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


from celery import uuid
from flask import Blueprint, render_template, redirect, request
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Length

from app.tasks import celery
from app.utils import rank_required

bp = Blueprint("zipgrep", __name__)

from app.models import *
from app.tasks.zipgrep import search_in_releases


class SearchForm(FlaskForm):
	query = StringField(lazy_gettext("Text to find (regex)"), [InputRequired(), Length(6, 100)])
	file_filter = StringField(lazy_gettext("File filter"), [InputRequired(), Length(1, 100)], default="*.lua")
	remember_me = BooleanField(lazy_gettext("Remember me"), default=True)
	submit = SubmitField(lazy_gettext("Search"))


@bp.route("/zipgrep/", methods=["GET", "POST"])
@rank_required(UserRank.ADMIN)
def zipgrep_search():
	form = SearchForm(request.form)
	if form.validate_on_submit():
		task_id = uuid()
		search_in_releases.apply_async((form.query.data, form.file_filter.data), task_id=task_id)
		result_url = url_for("zipgrep.view_results", id=task_id)
		return redirect(url_for("tasks.check", id=task_id, r=result_url))

	return render_template("zipgrep/search.html", form=form)


@bp.route("/zipgrep/<id>/")
def view_results(id):
	result = celery.AsyncResult(id)
	if result.status != "SUCCESS" or isinstance(result.result, Exception):
		result_url = url_for("zipgrep.view_results", id=id)
		return redirect(url_for("tasks.check", id=id, r=result_url))

	matches = result.result["matches"]
	for match in matches:
		match["package"] = Package.query.filter(
				Package.name == match["package"]["name"],
				Package.author.has(username=match["package"]["author"])).one()

	return render_template("zipgrep/view_results.html", query=result.result["query"], matches=matches)
