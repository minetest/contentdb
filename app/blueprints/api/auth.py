# Content DB
# Copyright (C) 2019  rubenwardy
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

from flask import request, make_response, jsonify, abort
from app.models import APIToken
from functools import wraps

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
				abort(400)

			token = APIToken.query.filter_by(access_token=access_token).first()
			if token is None:
				abort(403)
		else:
			abort(403)

		return f(token=token, *args, **kwargs)

	return decorated_function
