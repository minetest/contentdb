from flask import *
from flask_user import *
from flask_login import login_user, logout_user
import flask_menu as menu
from flask_github import GitHub
from app import app, github
from app.models import *


@app.route("/user/github/start/")
def github_signin_page():
	return github.authorize("")


def _do_login_user(user, remember_me=False):
	def _call_or_get(v):
		if callable(v):
			return v()
		else:
			return v

	# User must have been authenticated
	if not user:
		return False

	user.active = True
	if not user.rank.atLeast(UserRank.NEW_MEMBER):
		user.rank = UserRank.NEW_MEMBER

	db.session.commit()

	# Check if user account has been disabled
	if not _call_or_get(user.is_active):
		flash("Your account has not been enabled.", "error")
		return False

	# Check if user has a confirmed email address
	user_manager = current_app.user_manager
	if user_manager.enable_email and user_manager.enable_confirm_email \
			and not current_app.user_manager.enable_login_without_confirm_email \
			and not user.has_confirmed_email():
		url = url_for("user.resend_confirm_email")
		flash("Your email address has not yet been confirmed", "error")
		return False

	# Use Flask-Login to sign in user
	login_user(user, remember=remember_me)
	signals.user_logged_in.send(current_app._get_current_object(), user=user)

	flash("You have signed in successfully.", "success")

	return True



def _login_user(user):
	user_mixin = None
	if user_manager.enable_username:
		user_mixin = user_manager.find_user_by_username(user.username)

	return _do_login_user(user_mixin, False)



@app.route("/user/github/callback/")
@github.authorized_handler
def github_authorized(oauth_token):
	next_url = request.args.get("next")
	if oauth_token is None:
		flash("Authorization failed [err=gh-oauth-login-failed]", "danger")
		return redirect(url_for("user.login"))

	import requests

	# Get Github username
	url = "https://api.github.com/user"
	r = requests.get(url, headers={"Authorization": "token " + oauth_token})
	username = r.json()["login"]

	# Get user by github username
	userByGithub = User.query.filter_by(github_username=username).first()

	# If logged in, connect
	if current_user and current_user.is_authenticated:
		if userByGithub is None:
			current_user.github_username = username
			db.session.add(auth)
			db.session.commit()
			return redirect(url_for("gitAccount", id=auth.id))
		else:
			flash("Github account is already associated with another user", "danger")
			return redirect(url_for("home_page"))

	# If not logged in, log in
	else:
		if userByGithub is None:
			newUser = User(username)
			newUser.github_username = username
			db.session.add(newUser)
			db.session.commit()

			if not _login_user(newUser):
				raise Exception("Unable to login as user we just created")

			flash("Created an account", "success")
			return redirect(url_for("user_profile_page", username=username))
		elif _login_user(userByGithub):
			return redirect(next_url or url_for("home_page"))
		else:
			flash("Authorization failed [err=gh-login-failed]", "danger")
			return redirect(url_for("user.login"))
