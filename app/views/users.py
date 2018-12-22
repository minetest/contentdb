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
from app import app
from app.models import *
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from app.utils import randomString, loginUser
from app.tasks.forumtasks import checkForumAccount
from app.tasks.emails import sendVerifyEmail
from app.tasks.phpbbparser import getProfile

# Define the User profile form
class UserProfileForm(FlaskForm):
	display_name = StringField("Display name", [Optional(), Length(2, 20)])
	email = StringField("Email", [Optional(), Email()])
	rank = SelectField("Rank", [Optional()], choices=UserRank.choices(), coerce=UserRank.coerce, default=UserRank.NEW_MEMBER)
	submit = SubmitField("Save")

@app.route("/users/", methods=["GET"])
@login_required
def user_list_page():
	users = User.query.order_by(db.desc(User.rank), db.asc(User.display_name)).all()
	return render_template("users/list.html", users=users)


@app.route("/users/<username>/", methods=["GET", "POST"])
def user_profile_page(username):
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

			if user.checkPerm(current_user, Permission.CHANGE_RANK):
				newRank = form["rank"].data
				if current_user.rank.atLeast(newRank):
					user.rank = form["rank"].data
				else:
					flash("Can't promote a user to a rank higher than yourself!", "error")

			if user.checkPerm(current_user, Permission.CHANGE_EMAIL):
				newEmail = form["email"].data
				if newEmail != user.email and newEmail.strip() != "":
					token = randomString(32)

					ver = UserEmailVerification()
					ver.user = user
					ver.token = token
					ver.email = newEmail
					db.session.add(ver)
					db.session.commit()

					task = sendVerifyEmail.delay(newEmail, token)
					return redirect(url_for("check_task", id=task.id, r=url_for("user_profile_page", username=username)))

			# Save user_profile
			db.session.commit()

			# Redirect to home page
			return redirect(url_for("user_profile_page", username=username))

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
	return render_template("users/user_profile_page.html",
			user=user, form=form, packages=packages, topics_to_add=topics_to_add)

class SetPasswordForm(FlaskForm):
	email = StringField("Email", [Optional(), Email()])
	password = PasswordField("New password", [InputRequired(), Length(2, 20)])
	password2 = PasswordField("Verify password", [InputRequired(), Length(2, 20)])
	submit = SubmitField("Save")

@app.route("/user/set-password/", methods=["GET", "POST"])
@login_required
def set_password_page():
	if current_user.password is not None:
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
			user_manager.update_password(current_user, hashed_password)

			# Send 'password_changed' email
			if user_manager.enable_email and user_manager.send_password_changed_email and current_user.email:
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
				return redirect(url_for("check_task", id=task.id, r=url_for("user_profile_page", username=current_user.username)))
			else:
				return redirect(url_for("user_profile_page", username=current_user.username))
		else:
			flash("Passwords do not match", "error")

	return render_template("users/set_password.html", form=form, optional=request.args.get("optional"))


@app.route("/user/claim/", methods=["GET", "POST"])
def user_claim_page():
	username = request.args.get("username")
	if username is None:
		username = ""
	else:
		method = request.args.get("method")
		user = User.query.filter_by(forums_username=username).first()
		if user and user.rank.atLeast(UserRank.NEW_MEMBER):
			flash("User has already been claimed", "error")
			return redirect(url_for("user_claim_page"))
		elif user is None and method == "github":
			flash("Unable to get Github username for user", "error")
			return redirect(url_for("user_claim_page"))
		elif user is None:
			flash("Unable to find that user", "error")
			return redirect(url_for("user_claim_page"))

		if user is not None and method == "github":
			return redirect(url_for("github_signin_page"))

	token = None
	if "forum_token" in session:
		token = session["forum_token"]
	else:
		token = randomString(32)
		session["forum_token"] = token

	if request.method == "POST":
		ctype	= request.form.get("claim_type")
		username = request.form.get("username")

		if username is None or len(username.strip()) < 2:
			flash("Invalid username", "error")
		elif ctype == "github":
			task = checkForumAccount.delay(username)
			return redirect(url_for("check_task", id=task.id, r=url_for("user_claim_page", username=username, method="github")))
		elif ctype == "forum":
			user = User.query.filter_by(forums_username=username).first()
			if user is not None and user.rank.atLeast(UserRank.NEW_MEMBER):
				flash("That user has already been claimed!", "error")
				return redirect(url_for("user_claim_page"))

			# Get signature
			sig = None
			try:
				profile = getProfile("https://forum.minetest.net", username)
				sig = profile.signature
			except IOError:
				flash("Unable to get forum signature - does the user exist?", "error")
				return redirect(url_for("user_claim_page", username=username))

			# Look for key
			if token in sig:
				if user is None:
					user = User(username)
					user.forums_username = username
					db.session.add(user)
					db.session.commit()

				if loginUser(user):
					return redirect(url_for("set_password_page"))
				else:
					flash("Unable to login as user", "error")
					return redirect(url_for("user_claim_page", username=username))

			else:
				flash("Could not find the key in your signature!", "error")
				return redirect(url_for("user_claim_page", username=username))
		else:
			flash("Unknown claim type", "error")

	return render_template("users/claim.html", username=username, key=token)

@app.route("/users/verify/")
def verify_email_page():
	token = request.args.get("token")
	ver = UserEmailVerification.query.filter_by(token=token).first()
	if ver is None:
		flash("Unknown verification token!", "error")
	else:
		ver.user.email = ver.email
		db.session.delete(ver)
		db.session.commit()

	if current_user.is_authenticated:
		return redirect(url_for("user_profile_page", username=current_user.username))
	else:
		return redirect(url_for("home_page"))
