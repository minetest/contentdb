# ContentDB
# Copyright (C) 2019  rubenwardy
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

from functools import wraps

from flask import request, abort

from app.models import APIToken
from .support import error


def is_api_authd(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		token = None

		value = request.headers.get("authorization")
		if value is None:
			pass
		elif value[0:7].lower() == "bearer ":
			access_token = value[7:]
			if len(access_token) < 10:
				error(400, "API token is too short")

			token = APIToken.query.filter_by(access_token=access_token).first()
			if token is None:
				error(403, "Unknown API token")
		else:
			error(403, "Unsupported authentication method")

		return f(token=token, *args, **kwargs)

	return decorated_function
