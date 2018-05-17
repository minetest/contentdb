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
import flask_menu as menu
from flask_github import GitHub
from app import app, github
from app.models import *
from app.utils import loginUser

@app.route("/user/github/start/")
def github_signin_page():
	return github.authorize("")

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
			flash("Unable to find an account for that Github user", "error")
			return redirect(url_for("user_claim_page"))
		elif loginUser(userByGithub):
			return redirect(next_url or url_for("home_page"))
		else:
			flash("Authorization failed [err=gh-login-failed]", "danger")
			return redirect(url_for("user.login"))
