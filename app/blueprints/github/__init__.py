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

from flask import Blueprint

bp = Blueprint("github", __name__)

from flask import redirect, url_for, request, flash, abort, render_template, jsonify
from flask_user import current_user, login_required
from sqlalchemy import func
from flask_github import GitHub
from app import github, csrf
from app.models import db, User, APIToken, Package, Permission
from app.utils import loginUser, randomString, abs_url_for
from app.blueprints.api.support import error, handleCreateRelease
import hmac, requests, json

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField

@bp.route("/github/start/")
def start():
	return github.authorize("", redirect_uri=url_for("github.callback"))

@bp.route("/github/callback/")
@github.authorized_handler
def callback(oauth_token):
	next_url = request.args.get("next")
	if oauth_token is None:
		flash("Authorization failed [err=gh-oauth-login-failed]", "danger")
		return redirect(url_for("user.login"))

	# Get Github username
	url = "https://api.github.com/user"
	r = requests.get(url, headers={"Authorization": "token " + oauth_token})
	username = r.json()["login"]

	# Get user by github username
	userByGithub = User.query.filter(func.lower(User.github_username) == func.lower(username)).first()

	# If logged in, connect
	if current_user and current_user.is_authenticated:
		if userByGithub is None:
			current_user.github_username = username
			db.session.commit()
			flash("Linked github to account", "success")
			return redirect(url_for("homepage.home"))
		else:
			flash("Github account is already associated with another user", "danger")
			return redirect(url_for("homepage.home"))

	# If not logged in, log in
	else:
		if userByGithub is None:
			flash("Unable to find an account for that Github user", "danger")
			return redirect(url_for("users.claim"))
		elif loginUser(userByGithub):
			if not current_user.hasPassword():
				return redirect(next_url or url_for("users.set_password", optional=True))
			else:
				return redirect(next_url or url_for("homepage.home"))
		else:
			flash("Authorization failed [err=gh-login-failed]", "danger")
			return redirect(url_for("user.login"))


@bp.route("/github/webhook/", methods=["POST"])
@csrf.exempt
def webhook():
	json = request.json

	# Get package
	github_url = "github.com/" + json["repository"]["full_name"]
	package = Package.query.filter(Package.repo.like("%{}%".format(github_url))).first()
	if package is None:
		return error(400, "Unknown package")

	# Get all tokens for package
	possible_tokens = APIToken.query.filter_by(package=package).all()
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
		return error(403, "Invalid authentication")

	if not package.checkPerm(actual_token.owner, Permission.APPROVE_RELEASE):
		return error(403, "Only trusted members can use webhooks")

	#
	# Check event
	#

	event = request.headers.get("X-GitHub-Event")
	if event == "push":
		ref = json["after"]
		title = json["head_commit"]["message"].partition("\n")[0]
	elif event == "create" and json["ref_type"] == "tag":
		ref = json["ref"]
		title = ref
	elif event == "ping":
		return jsonify({ "success": True, "message": "Ping successful" })
	else:
		return error(400, "Unsupported event. Only 'push', `create:tag`, and 'ping' are supported.")

	#
	# Perform release
	#

	return handleCreateRelease(actual_token, package, title, ref)


class SetupWebhookForm(FlaskForm):
	event   = SelectField("Event Type", choices=[('create', 'New tag'), ('push', 'Push')])
	submit  = SubmitField("Save")


@bp.route("/github/callback/webhook/")
@github.authorized_handler
def callback_webhook(oauth_token=None):
	pid = request.args.get("pid")
	if pid is None:
		abort(404)

	current_user.github_access_token = oauth_token
	db.session.commit()

	return redirect(url_for("github.setup_webhook", pid=pid))


@bp.route("/github/webhook/new/", methods=["GET", "POST"])
@login_required
def setup_webhook():
	pid = request.args.get("pid")
	if pid is None:
		abort(404)

	package = Package.query.get(pid)
	if package is None:
		abort(404)

	if not package.checkPerm(current_user, Permission.APPROVE_RELEASE):
		flash("Only trusted members can use webhooks", "danger")
		return redirect(package.getDetailsURL())

	gh_user, gh_repo = package.getGitHubFullName()
	if gh_user is None or gh_repo is None:
		flash("Unable to get Github full name from repo address", "danger")
		return redirect(package.getDetailsURL())

	if current_user.github_access_token is None:
		return github.authorize("write:repo_hook", \
			redirect_uri=abs_url_for("github.callback_webhook", pid=pid))

	form = SetupWebhookForm(formdata=request.form)
	if request.method == "POST" and form.validate():
		token = APIToken()
		token.name = "Github Webhook for " + package.title
		token.owner = current_user
		token.access_token = randomString(32)
		token.package = package

		event = form.event.data
		if event != "push" and event != "create":
			abort(500)

		if handleMakeWebhook(gh_user, gh_repo, package, \
				current_user.github_access_token, event, token):
			return redirect(package.getDetailsURL())
		else:
			return redirect(url_for("github.setup_webhook", pid=package.id))

	return render_template("github/setup_webhook.html", \
		form=form, package=package)


def handleMakeWebhook(gh_user, gh_repo, package, oauth, event, token):
	url = "https://api.github.com/repos/{}/{}/hooks".format(gh_user, gh_repo)
	headers = {
		"Authorization": "token " + oauth
	}
	data = {
		"name": "web",
		"active": True,
		"events": [event],
		"config": {
			"url": abs_url_for("github.webhook"),
			"content_type": "json",
			"secret": token.access_token
		},
	}

	# First check that the webhook doesn't already exist
	r = requests.get(url, headers=headers)

	if r.status_code == 401 or r.status_code == 403:
		current_user.github_access_token = None
		db.session.commit()
		return False

	if r.status_code != 200:
		flash("Failed to create webhook, received response from Github " +
			str(r.status_code) + ": " +
			str(r.json().get("message")), "danger")
		return False

	for hook in r.json():
		if hook.get("config") and hook["config"].get("url") and \
				hook["config"]["url"] == data["config"]["url"]:
			flash("Failed to create webhook, as it already exists", "danger")
			return False


	# Create it
	r = requests.post(url, headers=headers, data=json.dumps(data))

	if r.status_code == 201:
		db.session.add(token)
		db.session.commit()

		return True

	elif r.status_code == 401 or r.status_code == 403:
		current_user.github_access_token = None
		db.session.commit()

		return False

	else:
		flash("Failed to create webhook, received response from Github " +
			str(r.status_code) + ": " +
			str(r.json().get("message")), "danger")
		return False
