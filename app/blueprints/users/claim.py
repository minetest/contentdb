# ContentDB
# Copyright (C) 2018-21 rubenwardy
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
from flask_babel import gettext

from . import bp
from flask import redirect, render_template, session, request, flash, url_for
from app.models import db, User, UserRank
from app.utils import randomString, login_user_set_active, is_username_valid
from app.tasks.forumtasks import checkForumAccount
from app.utils.phpbbparser import getProfile


@bp.route("/user/claim/", methods=["GET", "POST"])
def claim():
	return render_template("users/claim.html")


@bp.route("/user/claim-forums/", methods=["GET", "POST"])
def claim_forums():
	username = request.args.get("username")
	if username is None:
		username = ""
	else:
		method = request.args.get("method")

		if not is_username_valid(username):
			flash(gettext("Invalid username, Only alphabetic letters (A-Za-z), numbers (0-9), underscores (_), minuses (-), and periods (.) allowed. Consider contacting an admin"), "danger")
			return redirect(url_for("users.claim_forums"))

		user = User.query.filter_by(forums_username=username).first()
		if user and user.rank.atLeast(UserRank.NEW_MEMBER):
			flash(gettext("User has already been claimed"), "danger")
			return redirect(url_for("users.claim_forums"))
		elif method == "github":
			if user is None or user.github_username is None:
				flash(gettext("Unable to get GitHub username for user"), "danger")
				return redirect(url_for("users.claim_forums", username=username))
			else:
				return redirect(url_for("github.start"))

	if "forum_token" in session:
		token = session["forum_token"]
	else:
		token = randomString(12)
		session["forum_token"] = token

	if request.method == "POST":
		ctype	= request.form.get("claim_type")
		username = request.form.get("username")

		if not is_username_valid(username):
			flash(gettext("Invalid username, Only alphabetic letters (A-Za-z), numbers (0-9), underscores (_), minuses (-), and periods (.) allowed. Consider contacting an admin"), "danger")
		elif ctype == "github":
			task = checkForumAccount.delay(username)
			return redirect(url_for("tasks.check", id=task.id, r=url_for("users.claim_forums", username=username, method="github")))
		elif ctype == "forum":
			user = User.query.filter_by(forums_username=username).first()
			if user is not None and user.rank.atLeast(UserRank.NEW_MEMBER):
				flash(gettext("That user has already been claimed!"), "danger")
				return redirect(url_for("users.claim_forums"))

			# Get signature
			try:
				profile = getProfile("https://forum.minetest.net", username)
				sig = profile.signature if profile else None
			except IOError as e:
				if hasattr(e, 'message'):
					message = e.message
				else:
					message = str(e)

				flash(gettext(u"Error whilst attempting to access forums: %(message)s", message=message), "danger")
				return redirect(url_for("users.claim_forums", username=username))

			if profile is None:
				flash(gettext("Unable to get forum signature - does the user exist?"), "danger")
				return redirect(url_for("users.claim_forums", username=username))

			# Look for key
			if sig and token in sig:
				# Try getting again to fix crash
				user = User.query.filter_by(forums_username=username).first()
				if user is None:
					user = User(username)
					user.forums_username = username
					db.session.add(user)
					db.session.commit()

				ret = login_user_set_active(user, remember=True)
				if ret is None:
					flash(gettext("Unable to login as user"), "danger")
					return redirect(url_for("users.claim_forums", username=username))

				return ret

			else:
				flash(gettext("Could not find the key in your signature!"), "danger")
				return redirect(url_for("users.claim_forums", username=username))
		else:
			flash(gettext("Unknown claim type"), "danger")

	return render_template("users/claim_forums.html", username=username, key="cdb_" + token)
