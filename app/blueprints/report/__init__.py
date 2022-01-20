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

from flask import Blueprint, request, render_template, url_for
from flask_babel import lazy_gettext
from flask_login import current_user
from flask_wtf import FlaskForm
from werkzeug.utils import redirect
from wtforms import TextAreaField, SubmitField, BooleanField
from wtforms.fields.html5 import URLField
from wtforms.validators import InputRequired, Optional, Length

from app.models import User, UserRank
from app.tasks.emails import send_user_email
from app.tasks.webhooktasks import post_discord_webhook
from app.utils import isYes, isNo

bp = Blueprint("report", __name__)


class ReportForm(FlaskForm):
	url = URLField(lazy_gettext("URL"), [Optional()])
	message = TextAreaField(lazy_gettext("Message"), [InputRequired(), Length(10, 10000)])
	submit = SubmitField(lazy_gettext("Report"))


@bp.route("/report/", methods=["GET", "POST"])
def report():
	is_anon = not current_user.is_authenticated or not isNo(request.args.get("anon"))

	form = ReportForm(formdata=request.form)
	if request.method == "GET":
		if "url" in request.args:
			form.url.data = request.args["url"]

	if form.validate_on_submit():
		if current_user.is_authenticated:
			user_info = f"{current_user.username}"
		else:
			user_info = request.headers.get("X-Forwarded-For") or request.remote_addr

		url = request.args.get("url") or form.url.data or "?"
		text = f"{url}\n\n{form.message.data}"

		task = None
		for admin in User.query.filter_by(rank=UserRank.ADMIN).all():
			task = send_user_email.delay(admin.email, f"User report from {user_info}", text)

		post_discord_webhook.delay(None if is_anon else current_user.username, f"**New Report**\n`{url}`\n\n{form.message.data}", True)

		return redirect(url_for("tasks.check", id=task.id, r=url_for("homepage.home")))

	return render_template("report/index.html", form=form, url=request.args.get("url"), is_anon=is_anon)
