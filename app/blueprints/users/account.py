# ContentDB
# Copyright (C) 2020  rubenwardy
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



from flask import *
from flask_login import current_user, login_required, logout_user, login_user
from flask_wtf import FlaskForm
from sqlalchemy import or_
from wtforms import *
from wtforms.validators import *

from app.models import *
from app.tasks.emails import send_verify_email, send_anon_email, send_unsubscribe_verify, send_user_email
from app.utils import randomString, make_flask_login_password, is_safe_url, check_password_hash, addAuditLog, nonEmptyOrNone, post_login
from passlib.pwd import genphrase

from . import bp


class LoginForm(FlaskForm):
	username = StringField("Username or email", [InputRequired()])
	password = PasswordField("Password", [InputRequired(), Length(6, 100)])
	remember_me = BooleanField("Remember me", default=True)
	submit = SubmitField("Sign in")


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

	addAuditLog(AuditSeverity.USER, user, "Logged in using password",
			url_for("users.profile", username=user.username))
	db.session.commit()

	if not login_user(user, remember=form.remember_me.data):
		flash("Login failed", "danger")
		return

	return post_login(user, request.args.get("next"))


@bp.route("/user/login/", methods=["GET", "POST"])
def login():
	if current_user.is_authenticated:
		next = request.args.get("next")
		if next and not is_safe_url(next):
			abort(400)

		return redirect(next or url_for("homepage.home"))

	form = LoginForm(request.form)
	if form.validate_on_submit():
		ret = handle_login(form)
		if ret:
			return ret

	if request.method == "GET":
		form.remember_me.data = True


	return render_template("users/login.html", form=form)


@bp.route("/user/logout/", methods=["GET", "POST"])
def logout():
	logout_user()
	return redirect(url_for("homepage.home"))


class RegisterForm(FlaskForm):
	display_name = StringField("Display Name", [Optional(), Length(1, 20)], filters=[nonEmptyOrNone])
	username = StringField("Username", [InputRequired(),
					Regexp("^[a-zA-Z0-9._-]+$", message="Only a-zA-Z0-9._ allowed")])
	email    = StringField("Email", [InputRequired(), Email()])
	password = PasswordField("Password", [InputRequired(), Length(6, 100)])
	question  = StringField("What is the result of the above calculation?", [InputRequired()])
	agree    = BooleanField("I agree", [DataRequired()])
	submit   = SubmitField("Register")


def handle_register(form):
	if form.question.data.strip().lower() != "19":
		flash("Incorrect captcha answer", "danger")
		return

	user_by_name = User.query.filter(or_(
			User.username == form.username.data,
			User.username == form.display_name.data,
			User.display_name == form.display_name.data,
			User.forums_username == form.username.data,
			User.github_username == form.username.data)).first()
	if user_by_name:
		if user_by_name.rank == UserRank.NOT_JOINED and user_by_name.forums_username:
			flash("An account already exists for that username but hasn't been claimed yet.", "danger")
			return redirect(url_for("users.claim_forums", username=user_by_name.forums_username))
		else:
			flash("That username/display name is already in use, please choose another.", "danger")
			return

	alias_by_name = PackageAlias.query.filter(or_(
			PackageAlias.author==form.username.data,
			PackageAlias.author==form.display_name.data)).first()
	if alias_by_name:
		flash("That username/display name is already in use, please choose another.", "danger")
		return

	user_by_email = User.query.filter_by(email=form.email.data).first()
	if user_by_email:
		send_anon_email.delay(form.email.data, "Email already in use",
				"We were unable to create the account as the email is already in use by {}. Try a different email address.".format(
						user_by_email.display_name))
		flash("Check your email address to verify your account", "success")
		return redirect(url_for("homepage.home"))
	elif EmailSubscription.query.filter_by(email=form.email.data, blacklisted=True).count() > 0:
		flash("That email address has been unsubscribed/blacklisted, and cannot be used", "danger")
		return

	user = User(form.username.data, False, form.email.data, make_flask_login_password(form.password.data))
	user.notification_preferences = UserNotificationPreferences(user)
	if form.display_name.data:
		user.display_name = form.display_name.data
	db.session.add(user)

	addAuditLog(AuditSeverity.USER, user, "Registered with email, display name=" + user.display_name,
			url_for("users.profile", username=user.username))

	token = randomString(32)

	ver = UserEmailVerification()
	ver.user = user
	ver.token = token
	ver.email = form.email.data
	db.session.add(ver)
	db.session.commit()

	send_verify_email.delay(form.email.data, token)

	flash("Check your email address to verify your account", "success")
	return redirect(url_for("homepage.home"))


@bp.route("/user/register/", methods=["GET", "POST"])
def register():
	form = RegisterForm(request.form)
	if form.validate_on_submit():
		ret = handle_register(form)
		if ret:
			return ret

	return render_template("users/register.html", form=form,
			suggested_password=genphrase(entropy=52, wordset="bip39"))


class ForgotPasswordForm(FlaskForm):
	email = StringField("Email", [InputRequired(), Email()])
	submit = SubmitField("Reset Password")

@bp.route("/user/forgot-password/", methods=["GET", "POST"])
def forgot_password():
	form = ForgotPasswordForm(request.form)
	if form.validate_on_submit():
		email = form.email.data
		user = User.query.filter_by(email=email).first()
		if user:
			token = randomString(32)

			addAuditLog(AuditSeverity.USER, user, "(Anonymous) requested a password reset",
					url_for("users.profile", username=user.username), None)

			ver = UserEmailVerification()
			ver.user = user
			ver.token = token
			ver.email = email
			ver.is_password_reset = True
			db.session.add(ver)
			db.session.commit()

			send_verify_email.delay(form.email.data, token)
		else:
			send_anon_email.delay(email, "Unable to find account", """
					<p>
						We were unable to perform the password reset as we could not find an account
						associated with this email.
					</p>
					<p>
						If you weren't expecting to receive this email, then you can safely ignore it.
					</p>
			""")

		flash("Check your email address to continue the reset", "success")
		return redirect(url_for("homepage.home"))

	return render_template("users/forgot_password.html", form=form)


class SetPasswordForm(FlaskForm):
	email = StringField("Email", [Optional(), Email()])
	password = PasswordField("New password", [InputRequired(), Length(8, 100)])
	password2 = PasswordField("Verify password", [InputRequired(), Length(8, 100), validators.EqualTo('password', message='Passwords must match')])
	submit = SubmitField("Save")

class ChangePasswordForm(FlaskForm):
	old_password = PasswordField("Old password", [InputRequired(), Length(8, 100)])
	password = PasswordField("New password", [InputRequired(), Length(8, 100)])
	password2 = PasswordField("Verify password", [InputRequired(), Length(8, 100), validators.EqualTo('password', message='Passwords must match')])
	submit = SubmitField("Save")


def handle_set_password(form):
	one = form.password.data
	two = form.password2.data
	if one != two:
		flash("Passwords do not much", "danger")
		return

	addAuditLog(AuditSeverity.USER, current_user, "Changed their password", url_for("users.profile", username=current_user.username))

	current_user.password = make_flask_login_password(form.password.data)

	if hasattr(form, "email"):
		newEmail = nonEmptyOrNone(form.email.data)
		if newEmail and newEmail != current_user.email:
			if EmailSubscription.query.filter_by(email=form.email.data, blacklisted=True).count() > 0:
				flash("That email address has been unsubscribed/blacklisted, and cannot be used", "danger")
				return

			token = randomString(32)

			ver = UserEmailVerification()
			ver.user = current_user
			ver.token = token
			ver.email = newEmail
			db.session.add(ver)

	db.session.commit()
	flash("Your password has been changed successfully.", "success")
	return redirect(url_for("homepage.home"))


@bp.route("/user/change-password/", methods=["GET", "POST"])
@login_required
def change_password():
	form = ChangePasswordForm(request.form)

	if form.validate_on_submit():
		if check_password_hash(current_user.password, form.old_password.data):
			ret = handle_set_password(form)
			if ret:
				return ret
		else:
			flash("Old password is incorrect", "danger")

	return render_template("users/change_set_password.html", form=form,
			suggested_password=genphrase(entropy=52, wordset="bip39"))


@bp.route("/user/set-password/", methods=["GET", "POST"])
@login_required
def set_password():
	if current_user.password:
		return redirect(url_for("users.change_password"))

	form = SetPasswordForm(request.form)
	if current_user.email is None:
		form.email.validators = [InputRequired(), Email()]

	if form.validate_on_submit():
		ret = handle_set_password(form)
		if ret:
			return ret

	return render_template("users/change_set_password.html", form=form, optional=request.args.get("optional"),
			suggested_password=genphrase(entropy=52, wordset="bip39"))


@bp.route("/user/verify/")
def verify_email():
	token = request.args.get("token")
	ver : UserEmailVerification = UserEmailVerification.query.filter_by(token=token).first()
	if ver is None:
		flash("Unknown verification token!", "danger")
		return redirect(url_for("homepage.home"))

	user = ver.user

	addAuditLog(AuditSeverity.USER, user, "Confirmed their email",
			url_for("users.profile", username=user.username))

	was_activating = not user.is_active

	if ver.email and user.email != ver.email:
		if User.query.filter_by(email=ver.email).count() > 0:
			flash("Another user is already using that email", "danger")
			return redirect(url_for("homepage.home"))

		flash("Confirmed email change", "success")

		if user.email:
			send_user_email.delay(user.email,
					"Email address changed",
					"Your email address has changed. If you didn't request this, please contact an administrator.")

	user.is_active = True
	user.email = ver.email

	db.session.delete(ver)
	db.session.commit()

	if ver.is_password_reset:
		login_user(user)
		user.password = None
		db.session.commit()

		return redirect(url_for("users.set_password"))

	if current_user.is_authenticated:
		return redirect(url_for("users.profile", username=current_user.username))
	elif was_activating:
		flash("You may now log in", "success")
		return redirect(url_for("users.login"))
	else:
		return redirect(url_for("homepage.home"))


class UnsubscribeForm(FlaskForm):
	email = StringField("Email", [InputRequired(), Email()])
	submit = SubmitField("Send")


def unsubscribe_verify():
	form = UnsubscribeForm(request.form)
	if form.validate_on_submit():
		email = form.email.data
		sub = EmailSubscription.query.filter_by(email=email).first()
		if not sub:
			sub = EmailSubscription(email)
			db.session.add(sub)

		sub.token = randomString(32)
		db.session.commit()
		send_unsubscribe_verify.delay(form.email.data)

		flash("Check your email address to continue the unsubscribe", "success")
		return redirect(url_for("homepage.home"))

	return render_template("users/unsubscribe.html", form=form)


def unsubscribe_manage(sub: EmailSubscription):
	user = User.query.filter_by(email=sub.email).first()

	if request.method == "POST":
		if user:
			user.email = None

		sub.blacklisted = True
		db.session.commit()

		flash("That email is now blacklisted. Please contact an admin if you wish to undo this.", "success")
		return redirect(url_for("homepage.home"))

	return render_template("users/unsubscribe.html", user=user)


@bp.route("/unsubscribe/", methods=["GET", "POST"])
def unsubscribe():
	token = request.args.get("token")
	if token:
		sub = EmailSubscription.query.filter_by(token=token).first()
		if sub:
			return unsubscribe_manage(sub)

	return unsubscribe_verify()
