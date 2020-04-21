# ContentDB
# Copyright (C) 2020  rubenwardy
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

from flask import Blueprint, request

bp = Blueprint("gitlab", __name__)

from app import csrf
from app.models import Package, APIToken, Permission
from app.blueprints.api.support import error, handleCreateRelease


@bp.route("/gitlab/webhook/", methods=["POST"])
@csrf.exempt
def webhook():
	json = request.json

	# Get package
	gitlab_url = "gitlab.com/{}/{}".format(json["project"]["namespace"], json["project"]["name"])
	package = Package.query.filter(Package.repo.like("%{}%".format(gitlab_url))).first()
	if package is None:
		return error(400, "Unknown package")

	# Get all tokens for package
	secret = request.headers.get("X-Gitlab-Token")
	if secret is None:
		return error(403, "Token required")

	token = APIToken.query.filter_by(access_token=secret).first()
	if secret is None:
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
	elif event == "tag_push":
		ref = json["ref"]
		title = ref.replace("refs/tags/", "")
	else:
		return error(400, "Unsupported event. Only 'push' and 'tag_push' are supported.")

	#
	# Perform release
	#

	return handleCreateRelease(token, package, title, ref)
