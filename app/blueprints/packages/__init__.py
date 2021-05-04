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

from app.models import User, Package, Permission

bp = Blueprint("packages", __name__)


def get_package_tabs(user: User, package: Package):
	if package is None or not package.checkPerm(user, Permission.EDIT_PACKAGE):
		return []

	return [
		{
			"id": "edit",
			"title": "Edit Details",
			"url": package.getEditURL()
		},
		{
			"id": "releases",
			"title": "Releases",
			"url": package.getReleaseListURL()
		},
		{
			"id": "screenshots",
			"title": "Screenshots",
			"url": package.getEditScreenshotsURL()
		},
		{
			"id": "maintainers",
			"title": "Maintainers",
			"url": package.getEditMaintainersURL()
		},
		{
			"id": "remove",
			"title": "Remove",
			"url": package.getRemoveURL()
		}
	]


from . import packages, screenshots, releases, reviews
