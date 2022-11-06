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

from app.models import User, Package, Permission, PackageType

bp = Blueprint("packages", __name__)


def get_package_tabs(user: User, package: Package):
	if package is None or not package.checkPerm(user, Permission.EDIT_PACKAGE):
		return []

	retval = [
		{
			"id": "edit",
			"title": gettext("Edit Details"),
			"url": package.getURL("packages.create_edit")
		},
		{
			"id": "releases",
			"title": gettext("Releases"),
			"url": package.getURL("packages.list_releases")
		},
		{
			"id": "screenshots",
			"title": gettext("Screenshots"),
			"url": package.getURL("packages.screenshots")
		},
		{
			"id": "maintainers",
			"title": gettext("Maintainers"),
			"url": package.getURL("packages.edit_maintainers")
		},
		{
			"id": "audit",
			"title": gettext("Audit Log"),
			"url": package.getURL("packages.audit")
		},
		{
			"id": "stats",
			"title": gettext("Statistics"),
			"url": package.getURL("packages.stats")
		},
		{
			"id": "share",
			"title": gettext("Share and Badges"),
			"url": package.getURL("packages.share")
		},
		{
			"id": "remove",
			"title": gettext("Remove"),
			"url": package.getURL("packages.remove")
		}
	]

	if package.type == PackageType.MOD:
		retval.insert(1, {
			"id": "game_support",
			"title": gettext("Supported Games"),
			"url": package.getURL("packages.game_support")
		})

	return retval


from . import packages, screenshots, releases, reviews, game_hub
