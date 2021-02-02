# ContentDB
# Copyright (C) 2021 rubenwardy
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



from app.logic.LogicError import LogicError
from app.models import User, Package, PackageType, MetaPackage, Tag, ContentWarning, db, Permission, NotificationType, AuditSeverity
from app.utils import addNotification, addAuditLog


def do_edit_package(user: User, package: Package, was_new: bool, data: dict, reason: str = None):
	if "name" in data and package.name != data["name"] and \
			not package.checkPerm(user, Permission.CHANGE_NAME):
		raise LogicError(403, "You do not have permission to change the package name")

	if not package.checkPerm(user, Permission.EDIT_PACKAGE):
		raise LogicError(403, "You do not have permission to edit this package")

	for alias, to in { "short_description": "short_desc" }.items():
		if alias in data:
			data[to] = data[alias]

	for key in ["name", "title", "short_desc", "desc", "type", "license", "media_license",
			"repo", "website", "issueTracker", "forums"]:
		if key in data:
			setattr(package, key, data[key])

	if package.type == PackageType.TXP:
		package.license = package.media_license

	if was_new and package.type == PackageType.MOD:
		m = MetaPackage.GetOrCreate(package.name, {})
		package.provides.append(m)

	package.tags.clear()

	if "tag" in data:
		for tag in data["tag"]:
			package.tags.append(Tag.query.get(tag))

	if "content_warnings" in data:
		package.content_warnings.clear()
		for warning in data["content_warnings"]:
			package.content_warnings.append(ContentWarning.query.get(warning))

	if not was_new:
		if reason is None:
			msg = "Edited {}".format(package.title)
		else:
			msg = "Edited {} ({})".format(package.title, reason)

		addNotification(package.maintainers, user, NotificationType.PACKAGE_EDIT,
				msg, package.getDetailsURL(), package)

		severity = AuditSeverity.NORMAL if user in package.maintainers else AuditSeverity.EDITOR
		addAuditLog(severity, user, msg, package.getDetailsURL(), package)

	db.session.commit()

	return package
