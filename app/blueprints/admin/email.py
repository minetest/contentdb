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
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *

from app.markdown import render_markdown
from app.models import *
from app.tasks.emails import send_user_email
from app.utils import rank_required, addAuditLog
from . import bp


class SendEmailForm(FlaskForm):
	subject = StringField("Subject", [InputRequired(), Length(1, 300)])
	text    = TextAreaField("Message", [InputRequired()])
	submit  = SubmitField("Send")


@bp.route("/admin/send-email/", methods=["GET", "POST"])
@rank_required(UserRank.ADMIN)
def send_single_email():
	username = request.args["username"]
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)

	next_url = url_for("users.profile", username=user.username)

	if user.email is None:
		flash("User has no email address!", "danger")
		return redirect(next_url)

	form = SendEmailForm(request.form)
	if form.validate_on_submit():
		addAuditLog(AuditSeverity.MODERATION, current_user,
				"Sent email to {}".format(user.display_name), url_for("users.profile", username=username))

		text = form.text.data
		html = render_markdown(text)
		task = send_user_email.delay([user.email], form.subject.data, text, html)
		return redirect(url_for("tasks.check", id=task.id, r=next_url))

	return render_template("admin/send_email.html", form=form, user=user)


@bp.route("/admin/send-bulk-email/", methods=["GET", "POST"])
@rank_required(UserRank.ADMIN)
def send_bulk_email():
	form = SendEmailForm(request.form)
	if form.validate_on_submit():
		addAuditLog(AuditSeverity.MODERATION, current_user,
				"Sent bulk email", None, None, form.text.data)

		text = form.text.data
		html = render_markdown(text)
		for user in User.query.filter(User.email != None).all():
			send_user_email.delay([user.email], form.subject.data, text, html)

		return redirect(url_for("admin.admin_page"))

	return render_template("admin/send_bulk_email.html", form=form)
