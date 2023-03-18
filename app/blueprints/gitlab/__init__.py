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

from flask import Blueprint, request, jsonify

bp = Blueprint("gitlab", __name__)

from app import csrf
from app.models import Package, APIToken, Permission, PackageState
from app.blueprints.api.support import error, api_create_vcs_release


def webhook_impl():
	json = request.json

	# Get package
	gitlab_url = json["project"]["web_url"].replace("https://", "").replace("http://", "")
	package = Package.query.filter(
		Package.repo.ilike("%{}%".format(gitlab_url)), Package.state != PackageState.DELETED).first()
	if package is None:
		return error(400,
				"Could not find package, did you set the VCS repo in CDB correctly? Expected {}".format(gitlab_url))

	# Get all tokens for package
	secret = request.headers.get("X-Gitlab-Token")
	if secret is None:
		return error(403, "Token required")

	token = APIToken.query.filter_by(access_token=secret).first()
	if token is None:
		return error(403, "Invalid authentication")

	if not package.checkPerm(token.owner, Permission.APPROVE_RELEASE):
		return error(403, "You do not have the permission to approve releases")

	#
	# Check event
	#

	event = json["event_name"]
	if event == "push":
		ref = json["after"]
		title = ref[:5]

		branch = json["ref"].replace("refs/heads/", "")
		if branch not in ["master", "main"]:
			return jsonify({"success": False,
				"message": "Webhook ignored, as it's not on the master/main branch"})

	elif event == "tag_push":
		ref = json["ref"]
		title = ref.replace("refs/tags/", "")
	else:
		return error(400, "Unsupported event: '{}'. Only 'push', 'create:tag', and 'ping' are supported."
					 .format(event or "null"))

	#
	# Perform release
	#

	if package.releases.filter_by(commit_hash=ref).count() > 0:
		return

	return api_create_vcs_release(token, package, title, ref, reason="Webhook")


@bp.route("/gitlab/webhook/", methods=["POST"])
@csrf.exempt
def webhook():
	try:
		return webhook_impl()
	except KeyError as err:
		return error(400, "Missing field: {}".format(err.args[0]))
