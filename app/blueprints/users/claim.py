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

from . import bp
from flask import redirect, render_template, session, request, flash, url_for
from app.models import db, User, UserRank
from app.utils import randomString, login_user_set_active
from app.tasks.forumtasks import checkForumAccount
from app.tasks.phpbbparser import getProfile
import re


def check_username(username):
	return username is not None and len(username) >= 2 and re.match("^[A-Za-z0-9._-]*$", username)


@bp.route("/user/claim/", methods=["GET", "POST"])
def claim():
	username = request.args.get("username")
	if username is None:
		username = ""
	else:
		method = request.args.get("method")

		if not check_username(username):
			flash("Invalid username - must only contain A-Za-z0-9._. Consider contacting an admin", "danger")
			return redirect(url_for("users.claim"))

		user = User.query.filter_by(forums_username=username).first()
		if user and user.rank.atLeast(UserRank.NEW_MEMBER):
			flash("User has already been claimed", "danger")
			return redirect(url_for("users.claim"))
		elif method == "github":
			if user is None or user.github_username is None:
				flash("Unable to get Github username for user", "danger")
				return redirect(url_for("users.claim", username=username))
			else:
				return redirect(url_for("github.start"))
		elif user is None and request.method == "POST":
			flash("Unable to find user", "danger")
			return redirect(url_for("users.claim"))

	if "forum_token" in session:
		token = session["forum_token"]
	else:
		token = randomString(32)
		session["forum_token"] = token

	if request.method == "POST":
		ctype	= request.form.get("claim_type")
		username = request.form.get("username")

		if not check_username(username):
			flash("Invalid username - must only contain A-Za-z0-9._. Consider contacting an admin", "danger")
		elif ctype == "github":
			task = checkForumAccount.delay(username)
			return redirect(url_for("tasks.check", id=task.id, r=url_for("users.claim", username=username, method="github")))
		elif ctype == "forum":
			user = User.query.filter_by(forums_username=username).first()
			if user is not None and user.rank.atLeast(UserRank.NEW_MEMBER):
				flash("That user has already been claimed!", "danger")
				return redirect(url_for("users.claim"))

			# Get signature
			sig = None
			try:
				profile = getProfile("https://forum.minetest.net", username)
				sig = profile.signature if profile else None
			except IOError as e:
				if hasattr(e, 'message'):
					message = e.message
				else:
					message = str(e)

				flash("Error whilst attempting to access forums: " + message, "danger")
				return redirect(url_for("users.claim", username=username))

			if profile is None:
				flash("Unable to get forum signature - does the user exist?", "danger")
				return redirect(url_for("users.claim", username=username))

			# Look for key
			if sig and token in sig:
				# Try getting again to fix crash
				user = User.query.filter_by(forums_username=username).first()
				if user is None:
					user = User(username)
					user.forums_username = username
					db.session.add(user)
					db.session.commit()

				if login_user_set_active(user, remember=True):
					return redirect(url_for("users.set_password"))
				else:
					flash("Unable to login as user", "danger")
					return redirect(url_for("users.claim", username=username))

			else:
				flash("Could not find the key in your signature!", "danger")
				return redirect(url_for("users.claim", username=username))
		else:
			flash("Unknown claim type", "danger")

	return render_template("users/claim.html", username=username, key="cdb_" + token)
