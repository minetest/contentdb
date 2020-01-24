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
from flask_login import login_user, logout_user
from app.markdown import render_markdown
from . import bp
from app.models import *
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from app.utils import randomString, loginUser, rank_required
from app.tasks.forumtasks import checkForumAccount
from app.tasks.emails import sendVerifyEmail, sendEmailRaw
from app.tasks.phpbbparser import getProfile

# Define the User profile form
class UserProfileForm(FlaskForm):
	display_name = StringField("Display name", [Optional(), Length(2, 20)])
	email = StringField("Email", [Optional(), Email()], filters = [lambda x: x or None])
	website_url = StringField("Website URL", [Optional(), URL()], filters = [lambda x: x or None])
	donate_url = StringField("Donation URL", [Optional(), URL()], filters = [lambda x: x or None])
	rank = SelectField("Rank", [Optional()], choices=UserRank.choices(), coerce=UserRank.coerce, default=UserRank.NEW_MEMBER)
	submit = SubmitField("Save")


@bp.route("/users/", methods=["GET"])
def list_all():
	users = User.query.order_by(db.desc(User.rank), db.asc(User.display_name)).all()
	return render_template("users/list.html", users=users)


@bp.route("/users/<username>/", methods=["GET", "POST"])
def profile(username):
	user = User.query.filter_by(username=username).first()
	if not user:
		abort(404)

	form = None
	if user.checkPerm(current_user, Permission.CHANGE_DNAME) or \
			user.checkPerm(current_user, Permission.CHANGE_EMAIL) or \
			user.checkPerm(current_user, Permission.CHANGE_RANK):
		# Initialize form
		form = UserProfileForm(formdata=request.form, obj=user)

		# Process valid POST
		if request.method=="POST" and form.validate():
			# Copy form fields to user_profile fields
			if user.checkPerm(current_user, Permission.CHANGE_DNAME):
				user.display_name = form["display_name"].data
				user.website_url  = form["website_url"].data
				user.donate_url   = form["donate_url"].data

			if user.checkPerm(current_user, Permission.CHANGE_RANK):
				newRank = form["rank"].data
				if current_user.rank.atLeast(newRank):
					user.rank = form["rank"].data
				else:
					flash("Can't promote a user to a rank higher than yourself!", "danger")

			if user.checkPerm(current_user, Permission.CHANGE_EMAIL):
				newEmail = form["email"].data
				if newEmail != user.email and newEmail.strip() != "":
					token = randomString(32)

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

			# Redirect to home page
			return redirect(url_for("users.profile", username=username))

	packages = user.packages.filter_by(soft_deleted=False)
	if not current_user.is_authenticated or (user != current_user and not current_user.canAccessTodoList()):
		packages = packages.filter_by(approved=True)
	packages = packages.order_by(db.asc(Package.title))

	topics_to_add = None
	if current_user == user or user.checkPerm(current_user, Permission.CHANGE_AUTHOR):
		topics_to_add = ForumTopic.query \
					.filter_by(author_id=user.id) \
					.filter(~ db.exists().where(Package.forums==ForumTopic.topic_id)) \
					.order_by(db.asc(ForumTopic.name), db.asc(ForumTopic.title)) \
					.all()

	# Process GET or invalid POST
	return render_template("users/profile.html",
			user=user, form=form, packages=packages, topics_to_add=topics_to_add)


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
		text = form.text.data
		html = render_markdown(text)
		task = sendEmailRaw.delay([user.email], form.subject.data, text, html)
		return redirect(url_for("tasks.check", id=task.id, r=next_url))

	return render_template("users/send_email.html", form=form)



class SetPasswordForm(FlaskForm):
	email = StringField("Email", [Optional(), Email()])
	password = PasswordField("New password", [InputRequired(), Length(2, 100)])
	password2 = PasswordField("Verify password", [InputRequired(), Length(2, 100)])
	submit = SubmitField("Save")

@bp.route("/user/set-password/", methods=["GET", "POST"])
@login_required
def set_password():
	if current_user.hasPassword():
		return redirect(url_for("user.change_password"))

	form = SetPasswordForm(request.form)
	if current_user.email == None:
		form.email.validators = [InputRequired(), Email()]

	if request.method == "POST" and form.validate():
		one = form.password.data
		two = form.password2.data
		if one == two:
			# Hash password
			hashed_password = user_manager.hash_password(form.password.data)

			# Change password
			current_user.password = hashed_password
			db.session.commit()

			# Send 'password_changed' email
			if user_manager.USER_ENABLE_EMAIL and current_user.email:
				emails.send_password_changed_email(current_user)

			# Send password_changed signal
			signals.user_changed_password.send(current_app._get_current_object(), user=current_user)

			# Prepare one-time system message
			flash('Your password has been changed successfully.', 'success')

			newEmail = form["email"].data
			if newEmail != current_user.email and newEmail.strip() != "":
				token = randomString(32)

				ver = UserEmailVerification()
				ver.user = current_user
				ver.token = token
				ver.email = newEmail
				db.session.add(ver)
				db.session.commit()

				task = sendVerifyEmail.delay(newEmail, token)
				return redirect(url_for("tasks.check", id=task.id, r=url_for("users.profile", username=current_user.username)))
			else:
				return redirect(url_for("user.login"))
		else:
			flash("Passwords do not match", "danger")

	return render_template("users/set_password.html", form=form, optional=request.args.get("optional"))


@bp.route("/users/verify/")
def verify_email():
	token = request.args.get("token")
	ver = UserEmailVerification.query.filter_by(token=token).first()
	if ver is None:
		flash("Unknown verification token!", "danger")
	else:
		ver.user.email = ver.email
		db.session.delete(ver)
		db.session.commit()

	if current_user.is_authenticated:
		return redirect(url_for("users.profile", username=current_user.username))
	else:
		return redirect(url_for("homepage.home"))
