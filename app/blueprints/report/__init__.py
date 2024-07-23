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

from flask import Blueprint, request, render_template, url_for, abort
from flask_babel import lazy_gettext
from flask_login import current_user
from flask_wtf import FlaskForm
from werkzeug.utils import redirect
from wtforms import TextAreaField, SubmitField
from wtforms.validators import InputRequired, Length

from app.models import User, UserRank
from app.tasks.emails import send_user_email
from app.tasks.webhooktasks import post_discord_webhook
from app.utils import is_no, abs_url_samesite, normalize_line_endings

bp = Blueprint("report", __name__)


class ReportForm(FlaskForm):
	message = TextAreaField(lazy_gettext("Message"), [InputRequired(), Length(10, 10000)], filters=[normalize_line_endings])
	submit = SubmitField(lazy_gettext("Report"))


@bp.route("/report/", methods=["GET", "POST"])
def report():
	is_anon = not current_user.is_authenticated or not is_no(request.args.get("anon"))

	url = request.args.get("url")
	if url:
		if url.startswith("/report/"):
			abort(404)

		url = abs_url_samesite(url)

	form = ReportForm(formdata=request.form) if current_user.is_authenticated else None
	if form and request.method == "GET":
		form.message.data = request.args.get("message", "")

	if form and form.validate_on_submit():
		if current_user.is_authenticated:
			user_info = f"{current_user.username}"
		else:
			user_info = request.headers.get("X-Forwarded-For") or request.remote_addr

		text = f"{url}\n\n{form.message.data}"

		task = None
		for admin in User.query.filter_by(rank=UserRank.ADMIN).all():
			task = send_user_email.delay(admin.email, admin.locale or "en",
					f"User report from {user_info}", text)

		post_discord_webhook.delay(None if is_anon else current_user.username, f"**New Report**\n{url}\n\n{form.message.data}", True)

		return redirect(url_for("tasks.check", id=task.id, r=url_for("homepage.home")))

	return render_template("report/index.html", form=form, url=url, is_anon=is_anon, noindex=url is not None)
