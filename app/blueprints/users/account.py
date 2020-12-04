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
from flask_login import current_user, login_required, logout_user, login_user
from flask_wtf import FlaskForm
from sqlalchemy import or_
from wtforms import *
from wtforms.validators import *

from app.models import *
from app.tasks.emails import sendVerifyEmail
from app.utils import randomString, make_flask_login_password, is_safe_url, check_password_hash
from . import bp


class LoginForm(FlaskForm):
	username = StringField("Username or email", [InputRequired()])
	password = PasswordField("Password", [InputRequired(), Length(6, 100)])
	remember_me = BooleanField("Remember me")
	submit = SubmitField("Login")


def handle_login(form):
	def show_safe_err(err):
		if "@" in username:
			flash("Incorrect email or password", "danger")
		else:
			flash(err, "danger")


	username = form.username.data.strip()
	user = User.query.filter(or_(User.username == username, User.email == username)).first()
	if user is None:
		return show_safe_err("User {} does not exist".format(username))

	if not check_password_hash(user.password, form.password.data):
		return show_safe_err("Incorrect password. Did you set one?")

	if not user.is_active:
		flash("You need to confirm the registration email", "danger")
		return


	login_user(user)
	flash("Logged in successfully.", "success")

	next = request.args.get("next")
	if next and not is_safe_url(next):
		abort(400)

	return redirect(next or url_for("homepage.home"))


@bp.route("/user/login/", methods=["GET", "POST"])
def login():
	form = LoginForm(request.form)
	if form.validate_on_submit():
		ret = handle_login(form)
		if ret:
			return ret


	return render_template("users/login.html", form=form)


@bp.route("/user/logout/", methods=["GET", "POST"])
def logout():
	logout_user()
	return redirect(url_for("homepage.home"))


class RegisterForm(FlaskForm):
	username = StringField("Username", [InputRequired()])
	email = StringField("Email", [InputRequired(), Email()])
	password = PasswordField("Password", [InputRequired(), Length(6, 100)])
	submit = SubmitField("Register")


@bp.route("/user/register/", methods=["GET", "POST"])
def register():
	form = RegisterForm(request.form)
	if form.validate_on_submit():
		user = User(form.username.data, False, form.email.data, make_flask_login_password(form.password.data))
		db.session.add(user)

		token = randomString(32)

		ver = UserEmailVerification()
		ver.user = user
		ver.token = token
		ver.email = form.email.data
		db.session.add(ver)
		db.session.commit()

		sendVerifyEmail.delay(form.email.data, token)

		flash("Check your email address to verify your account", "success")
		return redirect(url_for("homepage.home"))

	return render_template("users/register.html", form=form)


class ForgotPassword(FlaskForm):
	email = StringField("Email", [InputRequired(), Email()])
	submit = SubmitField("Reset Password")

@bp.route("/user/forgot-password/", methods=["GET", "POST"])
def forgot_password():
	form = ForgotPassword(request.form)
	if form.validate_on_submit():
		pass

	return "Forgot password page"


class SetPasswordForm(FlaskForm):
	email = StringField("Email", [Optional(), Email()])
	password = PasswordField("New password", [InputRequired(), Length(8, 100)])
	password2 = PasswordField("Verify password", [InputRequired(), Length(8, 100)])
	submit = SubmitField("Save")

@bp.route("/user/change-password/", methods=["GET", "POST"])
@login_required
def change_password():
	return "change"


@bp.route("/user/set-password/", methods=["GET", "POST"])
@login_required
def set_password():
	if current_user.hasPassword():
		return redirect(url_for("users.change_password"))

	form = SetPasswordForm(request.form)
	if current_user.email is None:
		form.email.validators = [InputRequired(), Email()]

	if request.method == "POST" and form.validate():
		one = form.password.data
		two = form.password2.data
		if one == two:
			# Hash password
			hashed_password = make_flask_login_password(form.password.data)

			# Change password
			current_user.password = hashed_password
			db.session.commit()

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
				return redirect(url_for("users.login"))
		else:
			flash("Passwords do not match", "danger")

	return render_template("users/set_password.html", form=form, optional=request.args.get("optional"))


@bp.route("/user/verify/")
def verify_email():
	token = request.args.get("token")
	ver = UserEmailVerification.query.filter_by(token=token).first()
	if ver is None:
		flash("Unknown verification token!", "danger")
		return redirect(url_for("homepage.home"))

	was_activating = not ver.user.is_active
	ver.user.is_active = True
	ver.user.email = ver.email
	db.session.delete(ver)
	db.session.commit()

	if current_user.is_authenticated:
		return redirect(url_for("users.profile", username=current_user.username))
	elif was_activating:
		flash("You may now log in", "success")
		return redirect(url_for("users.login"))
	else:
		return redirect(url_for("homepage.home"))
