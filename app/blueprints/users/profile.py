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
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from sqlalchemy import func
from wtforms import *
from wtforms.validators import *

from app.markdown import render_markdown
from app.models import *
from app.tasks.emails import sendVerifyEmail, sendEmailRaw
from app.tasks.forumtasks import checkForumAccount
from app.utils import randomString, rank_required, nonEmptyOrNone, addAuditLog, make_flask_login_password
from . import bp


# Define the User profile form
class UserProfileForm(FlaskForm):
	display_name = StringField("Display name", [Optional(), Length(2, 100)])
	forums_username = StringField("Forums Username", [Optional(), Length(2, 50)])
	github_username = StringField("GitHub Username", [Optional(), Length(2, 50)])
	email = StringField("Email", [Optional(), Email()], filters = [lambda x: x or None])
	website_url = StringField("Website URL", [Optional(), URL()], filters = [lambda x: x or None])
	donate_url = StringField("Donation URL", [Optional(), URL()], filters = [lambda x: x or None])
	rank = SelectField("Rank", [Optional()], choices=UserRank.choices(), coerce=UserRank.coerce, default=UserRank.NEW_MEMBER)
	submit = SubmitField("Save")


@bp.route("/users/", methods=["GET"])
def list_all():
	users = db.session.query(User, func.count(Package.id)) \
			.select_from(User).outerjoin(Package) \
			.order_by(db.desc(User.rank), db.asc(User.display_name)) \
			.group_by(User.id).all()

	return render_template("users/list.html", users=users)


@bp.route("/users/<username>/")
def profile(username):
	user = User.query.filter_by(username=username).first()
	if not user:
		abort(404)

	packages = user.packages.filter(Package.state != PackageState.DELETED)
	if not current_user.is_authenticated or (user != current_user and not current_user.canAccessTodoList()):
		packages = packages.filter_by(state=PackageState.APPROVED)
	packages = packages.order_by(db.asc(Package.title))

	topics_to_add = None
	if current_user == user or user.checkPerm(current_user, Permission.CHANGE_AUTHOR):
		topics_to_add = ForumTopic.query \
			.filter_by(author_id=user.id) \
			.filter(~ db.exists().where(Package.forums == ForumTopic.topic_id)) \
			.order_by(db.asc(ForumTopic.name), db.asc(ForumTopic.title)) \
			.all()

	# Process GET or invalid POST
	return render_template("users/profile.html",
			user=user, packages=packages, topics_to_add=topics_to_add)


def get_setting_tabs():
	return [
		{
			"id": "edit_profile",
			"title": "Edit Profile",
			"url": url_for("users.profile_edit", username=current_user.username)
		},
		{
			"id": "api_tokens",
			"title": "API Tokens",
			"url": url_for("api.list_tokens", username=current_user.username)
		},
	]


@bp.route("/users/<username>/edit/", methods=["GET", "POST"])
def profile_edit(username):
	user : User = User.query.filter_by(username=username).first()
	if not user:
		abort(404)

	if not user.can_see_edit_profile(current_user):
		flash("Permission denied", "danger")
		return redirect(url_for("users.profile", username=username))


	form = UserProfileForm(formdata=request.form, obj=user)

	# Process valid POST
	if request.method=="POST" and form.validate():
		severity = AuditSeverity.NORMAL if current_user == user else AuditSeverity.MODERATION
		addAuditLog(severity, current_user, "Edited {}'s profile".format(user.display_name),
				url_for("users.profile", username=username))

		# Copy form fields to user_profile fields
		if user.checkPerm(current_user, Permission.CHANGE_USERNAMES):
			user.display_name = form.display_name.data
			user.forums_username = nonEmptyOrNone(form.forums_username.data)
			user.github_username = nonEmptyOrNone(form.github_username.data)

		if user.checkPerm(current_user, Permission.CHANGE_PROFILE_URLS):
			user.website_url  = form["website_url"].data
			user.donate_url   = form["donate_url"].data

		if user.checkPerm(current_user, Permission.CHANGE_RANK):
			newRank = form["rank"].data
			if current_user.rank.atLeast(newRank):
				if newRank != user.rank:
					user.rank = form["rank"].data
					msg = "Set rank of {} to {}".format(user.display_name, user.rank.getTitle())
					addAuditLog(AuditSeverity.MODERATION, current_user, msg, url_for("users.profile", username=username))
			else:
				flash("Can't promote a user to a rank higher than yourself!", "danger")

		if user.checkPerm(current_user, Permission.CHANGE_EMAIL):
			newEmail = form["email"].data
			if newEmail and newEmail != user.email and newEmail.strip() != "":
				token = randomString(32)

				msg = "Changed email of {}".format(user.display_name)
				addAuditLog(severity, current_user, msg, url_for("users.profile", username=username))

				ver = UserEmailVerification()
				ver.user  = user
				ver.token = token
				ver.email = newEmail
				db.session.add(ver)
				db.session.commit()

				task = sendVerifyEmail.delay(newEmail, token)
				return redirect(url_for("tasks.check", id=task.id, r=url_for("users.profile", username=username)))

		# Save user_profile
		db.session.commit()

		return redirect(url_for("users.profile", username=username))

	# Process GET or invalid POST
	return render_template("users/profile_edit.html", user=user, form=form, tabs=get_setting_tabs(), current_tab="edit_profile")


@bp.route("/users/<username>/check/", methods=["POST"])
@login_required
def user_check(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)

	if current_user != user and not current_user.rank.atLeast(UserRank.MODERATOR):
		abort(403)

	if user.forums_username is None:
		abort(404)

	task = checkForumAccount.delay(user.forums_username)
	next_url = url_for("users.profile", username=username)

	return redirect(url_for("tasks.check", id=task.id, r=next_url))


class SendEmailForm(FlaskForm):
	subject = StringField("Subject", [InputRequired(), Length(1, 300)])
	text    = TextAreaField("Message", [InputRequired()])
	submit  = SubmitField("Send")


@bp.route("/users/<username>/email/", methods=["GET", "POST"])
@rank_required(UserRank.MODERATOR)
def send_email(username):
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
		task = sendEmailRaw.delay([user.email], form.subject.data, text, html)
		return redirect(url_for("tasks.check", id=task.id, r=next_url))

	return render_template("users/send_email.html", form=form)
