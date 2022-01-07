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
from flask_babel import gettext, lazy_gettext
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
	username = StringField(lazy_gettext("Username or email"), [InputRequired()])
	password = PasswordField(lazy_gettext("Password"), [InputRequired(), Length(6, 100)])
	remember_me = BooleanField(lazy_gettext("Remember me"), default=True)
	submit = SubmitField(lazy_gettext("Sign in"))


def handle_login(form):
	def show_safe_err(err):
		if "@" in username:
			flash(gettext("Incorrect email or password"), "danger")
		else:
			flash(err, "danger")


	username = form.username.data.strip()
	user = User.query.filter(or_(User.username == username, User.email == username)).first()
	if user is None:
		return show_safe_err(gettext(u"User %(username)s does not exist", username=username))

	if not check_password_hash(user.password, form.password.data):
		return show_safe_err(gettext(u"Incorrect password. Did you set one?"))

	if not user.is_active:
		flash(gettext("You need to confirm the registration email"), "danger")
		return

	addAuditLog(AuditSeverity.USER, user, "Logged in using password",
			url_for("users.profile", username=user.username))
	db.session.commit()

	if not login_user(user, remember=form.remember_me.data):
		flash(gettext("Login failed"), "danger")
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
	display_name = StringField(lazy_gettext("Display Name"), [Optional(), Length(1, 20)], filters=[nonEmptyOrNone])
	username = StringField(lazy_gettext("Username"), [InputRequired(),
					Regexp("^[a-zA-Z0-9._-]+$", message=lazy_gettext("Only a-zA-Z0-9._ allowed"))])
	email    = StringField(lazy_gettext("Email"), [InputRequired(), Email()])
	password = PasswordField(lazy_gettext("Password"), [InputRequired(), Length(6, 100)])
	question  = StringField(lazy_gettext("What is the result of the above calculation?"), [InputRequired()])
	agree    = BooleanField(lazy_gettext("I agree"), [DataRequired()])
	submit   = SubmitField(lazy_gettext("Register"))


def handle_register(form):
	if form.question.data.strip().lower() != "19":
		flash(gettext("Incorrect captcha answer"), "danger")
		return

	user_by_name = User.query.filter(or_(
			User.username == form.username.data,
			User.username == form.display_name.data,
			User.display_name == form.display_name.data,
			User.forums_username == form.username.data,
			User.github_username == form.username.data)).first()
	if user_by_name:
		if user_by_name.rank == UserRank.NOT_JOINED and user_by_name.forums_username:
			flash(gettext("An account already exists for that username but hasn't been claimed yet."), "danger")
			return redirect(url_for("users.claim_forums", username=user_by_name.forums_username))
		else:
			flash(gettext("That username/display name is already in use, please choose another."), "danger")
			return

	alias_by_name = PackageAlias.query.filter(or_(
			PackageAlias.author==form.username.data,
			PackageAlias.author==form.display_name.data)).first()
	if alias_by_name:
		flash(gettext("That username/display name is already in use, please choose another."), "danger")
		return

	user_by_email = User.query.filter_by(email=form.email.data).first()
	if user_by_email:
		send_anon_email.delay(form.email.data, "Email already in use",
			gettext("We were unable to create the account as the email is already in use by %(display_name)s. Try a different email address.",
					display_name=user_by_email.display_name))
		return redirect(url_for("flatpage", path="email_sent"))
	elif EmailSubscription.query.filter_by(email=form.email.data, blacklisted=True).count() > 0:
		flash(gettext("That email address has been unsubscribed/blacklisted, and cannot be used"), "danger")
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

	return redirect(url_for("flatpage", path="email_sent"))


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
	email = StringField(lazy_gettext("Email"), [InputRequired(), Email()])
	submit = SubmitField(lazy_gettext("Reset Password"))

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
						This may be because you used another email with your account, or because you never 
						confirmed your email.
					</p>
					<p>
						You can use GitHub to log in if it is associated with your account.
						Otherwise, you may need to contact rubenwardy for help.
					</p>
					<p>
						If you weren't expecting to receive this email, then you can safely ignore it.
					</p>
			""")

		return redirect(url_for("flatpage", path="email_sent"))

	return render_template("users/forgot_password.html", form=form)


class SetPasswordForm(FlaskForm):
	email = StringField(lazy_gettext("Email"), [Optional(), Email()])
	password = PasswordField(lazy_gettext("New password"), [InputRequired(), Length(8, 100)])
	password2 = PasswordField(lazy_gettext("Verify password"), [InputRequired(), Length(8, 100),
			validators.EqualTo('password', message=lazy_gettext('Passwords must match'))])
	submit = SubmitField(lazy_gettext("Save"))

class ChangePasswordForm(FlaskForm):
	old_password = PasswordField(lazy_gettext("Old password"), [InputRequired(), Length(8, 100)])
	password = PasswordField(lazy_gettext("New password"), [InputRequired(), Length(8, 100)])
	password2 = PasswordField(lazy_gettext("Verify password"), [InputRequired(), Length(8, 100),
			validators.EqualTo('password', message=lazy_gettext('Passwords must match'))])
	submit = SubmitField(lazy_gettext("Save"))


def handle_set_password(form):
	one = form.password.data
	two = form.password2.data
	if one != two:
		flash(gettext("Passwords do not much"), "danger")
		return

	addAuditLog(AuditSeverity.USER, current_user, "Changed their password", url_for("users.profile", username=current_user.username))

	current_user.password = make_flask_login_password(form.password.data)

	if hasattr(form, "email"):
		newEmail = nonEmptyOrNone(form.email.data)
		if newEmail and newEmail != current_user.email:
			if EmailSubscription.query.filter_by(email=form.email.data, blacklisted=True).count() > 0:
				flash(gettext(u"That email address has been unsubscribed/blacklisted, and cannot be used"), "danger")
				return

			user_by_email = User.query.filter_by(email=form.email.data).first()
			if user_by_email:
				send_anon_email.delay(form.email.data, "Email already in use",
					gettext(u"We were unable to create the account as the email is already in use by %(display_name)s. Try a different email address.",
							display_name=user_by_email.display_name))
			else:
				token = randomString(32)

				ver = UserEmailVerification()
				ver.user = current_user
				ver.token = token
				ver.email = newEmail
				db.session.add(ver)
				db.session.commit()

				send_verify_email.delay(form.email.data, token)

			flash(gettext("Your password has been changed successfully."), "success")
			return redirect(url_for("flatpage", path="email_sent"))

	db.session.commit()
	flash(gettext("Your password has been changed successfully."), "success")
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
			flash(gettext("Old password is incorrect"), "danger")

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
	ver: UserEmailVerification = UserEmailVerification.query.filter_by(token=token).first()
	if ver is None:
		flash(gettext("Unknown verification token!"), "danger")
		return redirect(url_for("homepage.home"))

	delta = (datetime.datetime.now() - ver.created_at)
	delta: datetime.timedelta
	if delta.total_seconds() > 12*60*60:
		flash(gettext("Token has expired"), "danger")
		db.session.delete(ver)
		db.session.commit()
		return redirect(url_for("homepage.home"))

	user = ver.user

	addAuditLog(AuditSeverity.USER, user, "Confirmed their email",
			url_for("users.profile", username=user.username))

	was_activating = not user.is_active

	if ver.email and user.email != ver.email:
		if User.query.filter_by(email=ver.email).count() > 0:
			flash(gettext("Another user is already using that email"), "danger")
			return redirect(url_for("homepage.home"))

		flash(gettext("Confirmed email change"), "success")

		if user.email:
			send_user_email.delay(user.email,
					gettext("Email address changed"),
					gettext("Your email address has changed. If you didn't request this, please contact an administrator."))

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
		flash(gettext("You may now log in"), "success")
		return redirect(url_for("users.login"))
	else:
		return redirect(url_for("homepage.home"))


class UnsubscribeForm(FlaskForm):
	email = StringField(lazy_gettext("Email"), [InputRequired(), Email()])
	submit = SubmitField(lazy_gettext("Send"))


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

		return redirect(url_for("flatpage", path="email_sent"))

	return render_template("users/unsubscribe.html", form=form)


def unsubscribe_manage(sub: EmailSubscription):
	user = User.query.filter_by(email=sub.email).first()

	if request.method == "POST":
		if user:
			user.email = None

		sub.blacklisted = True
		db.session.commit()

		flash(gettext("That email is now blacklisted. Please contact an admin if you wish to undo this."), "success")
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
