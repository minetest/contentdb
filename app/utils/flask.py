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


from urllib.parse import urljoin, urlparse

import user_agents
from flask import request, abort
from werkzeug.datastructures import MultiDict

from app.models import *


def is_safe_url(target):
	ref_url = urlparse(request.host_url)
	test_url = urlparse(urljoin(request.host_url, target))
	return test_url.scheme in ('http', 'https') and \
		   ref_url.netloc == test_url.netloc


# These are given to Jinja in template_filters.py

def abs_url_for(path, **kwargs):
	scheme = "https" if app.config["BASE_URL"][:5] == "https" else "http"
	return url_for(path, _external=True, _scheme=scheme, **kwargs)

def abs_url(path):
	return urljoin(app.config["BASE_URL"], path)

def url_current(abs=False):
	args = MultiDict(request.args)
	dargs = dict(args.lists())
	dargs.update(request.view_args)
	if abs:
		return abs_url_for(request.endpoint, **dargs)
	else:
		return url_for(request.endpoint, **dargs)

def url_set_anchor(anchor):
	args = MultiDict(request.args)
	dargs = dict(args.lists())
	dargs.update(request.view_args)
	return url_for(request.endpoint, **dargs) + "#" + anchor

def url_set_query(**kwargs):
	if request.endpoint is None:
		return None

	args = MultiDict(request.args)

	for key, value in kwargs.items():
		if key == "_add":
			for key2, value_to_add in value.items():
				values = set(args.getlist(key2))
				values.add(value_to_add)
				args.setlist(key2, list(values))
		elif key == "_remove":
			for key2, value_to_remove in value.items():
				values = set(args.getlist(key2))
				values.discard(value_to_remove)
				args.setlist(key2, list(values))
		else:
			args.setlist(key, [ value ])


	dargs = dict(args.lists())
	if request.view_args:
		dargs.update(request.view_args)

	return url_for(request.endpoint, **dargs)

def get_int_or_abort(v, default=None):
	if v is None:
		return default

	try:
		return int(v or default)
	except ValueError:
		abort(400)

def is_user_bot():
	user_agent = request.headers.get('User-Agent')
	if user_agent is None:
		return True

	user_agent = user_agents.parse(user_agent)
	return user_agent.is_bot
