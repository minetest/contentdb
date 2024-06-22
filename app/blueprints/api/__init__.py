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

import json
from flask import Blueprint

from .support import error

bp = Blueprint("api", __name__)


from . import tokens, endpoints


@bp.errorhandler(400)
@bp.errorhandler(401)
@bp.errorhandler(403)
@bp.errorhandler(404)
def handle_exception(e):
	"""Return JSON instead of HTML for HTTP errors."""
	# start with the correct headers and status code from the error
	response = e.get_response()
	# replace the body with JSON
	response.data = json.dumps({
		"success": False,
		"code": e.code,
		"name": e.name,
		"description": e.description,
	})
	response.content_type = "application/json"
	return response


@bp.route("/api/<path:path>")
def page_not_found(path):
	error(404, "Endpoint or method not found")
