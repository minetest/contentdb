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

from flask import Blueprint
from flask_babel import gettext

bp = Blueprint("github", __name__)

from flask import redirect, url_for, request, flash, jsonify, current_app
from flask_login import current_user
from sqlalchemy import func, or_, and_
from app import github, csrf
from app.models import db, User, APIToken, Package, Permission, AuditSeverity, PackageState
from app.utils import abs_url_for, add_audit_log, login_user_set_active
from app.blueprints.api.support import error, api_create_vcs_release
import hmac, requests

@bp.route("/github/start/")
def start():
	return github.authorize("", redirect_uri=abs_url_for("github.callback"))

@bp.route("/github/view/")
def view_permissions():
	url = "https://github.com/settings/connections/applications/" + \
			current_app.config["GITHUB_CLIENT_ID"]
	return redirect(url)


@bp.route("/github/callback/")
@github.authorized_handler
def callback(oauth_token):
	if oauth_token is None:
		flash(gettext("Authorization failed [err=gh-oauth-login-failed]"), "danger")
		return redirect(url_for("users.login"))

	# Get GitGub username
	url = "https://api.github.com/user"
	r = requests.get(url, headers={"Authorization": "token " + oauth_token})
	username = r.json()["login"]

	# Get user by GitHub username
	userByGithub = User.query.filter(func.lower(User.github_username) == func.lower(username)).first()

	# If logged in, connect
	if current_user and current_user.is_authenticated:
		if userByGithub is None:
			current_user.github_username = username
			db.session.commit()
			flash(gettext("Linked GitHub to account"), "success")
			return redirect(url_for("homepage.home"))
		else:
			flash(gettext("GitHub account is already associated with another user"), "danger")
			return redirect(url_for("homepage.home"))

	# If not logged in, log in
	else:
		if userByGithub is None:
			flash(gettext("Unable to find an account for that GitHub user"), "danger")
			return redirect(url_for("users.claim_forums"))

		ret = login_user_set_active(userByGithub, remember=True)
		if ret is None:
			flash(gettext("Authorization failed [err=gh-login-failed]"), "danger")
			return redirect(url_for("users.login"))

		add_audit_log(AuditSeverity.USER, userByGithub, "Logged in using GitHub OAuth",
					  url_for("users.profile", username=userByGithub.username))
		db.session.commit()
		return ret


@bp.route("/github/webhook/", methods=["POST"])
@csrf.exempt
def webhook():
	json = request.json

	# Get package
	github_url = "github.com/" + json["repository"]["full_name"]
	package = Package.query.filter(
		Package.repo.ilike("%{}%".format(github_url)), Package.state != PackageState.DELETED).first()
	if package is None:
		return error(400, "Could not find package, did you set the VCS repo in CDB correctly? Expected {}".format(github_url))

	# Get all tokens for package
	tokens_query = APIToken.query.filter(or_(APIToken.package==package,
			and_(APIToken.package==None, APIToken.owner==package.author)))

	possible_tokens = tokens_query.all()
	actual_token = None

	#
	# Check signature
	#

	header_signature = request.headers.get('X-Hub-Signature')
	if header_signature is None:
		return error(403, "Expected payload signature")

	sha_name, signature = header_signature.split('=')
	if sha_name != 'sha1':
		return error(403, "Expected SHA1 payload signature")

	for token in possible_tokens:
		mac = hmac.new(token.access_token.encode("utf-8"), msg=request.data, digestmod='sha1')

		if hmac.compare_digest(str(mac.hexdigest()), signature):
			actual_token = token
			break

	if actual_token is None:
		return error(403, "Invalid authentication, couldn't validate API token")

	if not package.check_perm(actual_token.owner, Permission.APPROVE_RELEASE):
		return error(403, "You do not have the permission to approve releases")

	#
	# Check event
	#

	event = request.headers.get("X-GitHub-Event")
	if event == "push":
		ref = json["after"]
		title = json["head_commit"]["message"].partition("\n")[0]
		branch = json["ref"].replace("refs/heads/", "")
		if branch not in [ "master", "main" ]:
			return jsonify({ "success": False, "message": "Webhook ignored, as it's not on the master/main branch" })

	elif event == "create":
		ref_type = json.get("ref_type")
		if ref_type != "tag":
			return jsonify({
					"success": False,
					"message": "Webhook ignored, as it's a non-tag create event. ref_type='{}'.".format(ref_type)
			})

		ref = json["ref"]
		title = ref

	elif event == "ping":
		return jsonify({ "success": True, "message": "Ping successful" })

	else:
		return error(400, "Unsupported event: '{}'. Only 'push', 'create:tag', and 'ping' are supported."
				.format(event or "null"))

	#
	# Perform release
	#

	if package.releases.filter_by(commit_hash=ref).count() > 0:
		return

	return api_create_vcs_release(actual_token, package, title, ref, reason="Webhook")
