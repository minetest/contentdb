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


import re
import validators

from app.logic.LogicError import LogicError
from app.models import User, Package, PackageType, MetaPackage, Tag, ContentWarning, db, Permission, AuditSeverity, License, UserRank
from app.utils import addAuditLog


def check(cond: bool, msg: str):
	if not cond:
		raise LogicError(400, msg)


def get_license(name):
	if type(name) == License:
		return name

	license = License.query.filter(License.name.ilike(name)).first()
	if license is None:
		raise LogicError(400, "Unknown license: " + name)
	return license


name_re = re.compile("^[a-z0-9_]+$")

AnyType = "?"
ALLOWED_FIELDS = {
	"type": AnyType,
	"title": str,
	"name": str,
	"short_description": str,
	"short_desc": str,
	"tags": list,
	"content_warnings": list,
	"license": AnyType,
	"media_license": AnyType,
	"long_description": str,
	"desc": str,
	"repo": str,
	"website": str,
	"issue_tracker": str,
	"issueTracker": str,
	"forums": int,
}

ALIASES = {
	"short_description": "short_desc",
	"issue_tracker": "issueTracker",
	"long_description": "desc"
}


def is_int(val):
	try:
		int(val)
		return True
	except ValueError:
		return False


def validate(data: dict):
	for key, value in data.items():
		if value is not None:
			typ = ALLOWED_FIELDS.get(key)
			check(typ is not None, key + " is not a known field")
			if typ != AnyType:
				check(isinstance(value, typ), key + " must be a " + typ.__name__)

	if "name" in data:
		name = data["name"]
		check(isinstance(name, str), "Name must be a string")
		check(bool(name_re.match(name)),
			"Name can only contain lower case letters (a-z), digits (0-9), and underscores (_)")

	for key in ["repo", "website", "issue_tracker", "issueTracker"]:
		value = data.get(key)
		if value is not None:
			check(value.startswith("http://") or value.startswith("https://"),
					key + " must start with http:// or https://")

			check(validators.url(value, public=True), key + " must be a valid URL")


def do_edit_package(user: User, package: Package, was_new: bool, was_web: bool, data: dict,
		reason: str = None):
	if not package.checkPerm(user, Permission.EDIT_PACKAGE):
		raise LogicError(403, "You do not have permission to edit this package")

	if "name" in data and package.name != data["name"] and \
			not package.checkPerm(user, Permission.CHANGE_NAME):
		raise LogicError(403, "You do not have permission to change the package name")

	for alias, to in ALIASES.items():
		if alias in data:
			data[to] = data[alias]

	validate(data)

	if "type" in data:
		data["type"] = PackageType.coerce(data["type"])

	if "license" in data:
		data["license"] = get_license(data["license"])

	if "media_license" in data:
		data["media_license"] = get_license(data["media_license"])

	for key in ["name", "title", "short_desc", "desc", "type", "license", "media_license",
			"repo", "website", "issueTracker", "forums"]:
		if key in data:
			setattr(package, key, data[key])

	if package.type == PackageType.TXP:
		package.license = package.media_license

	if was_new and package.type == PackageType.MOD:
		m = MetaPackage.GetOrCreate(package.name, {})
		package.provides.append(m)

	if "tags" in data:
		old_tags = list(package.tags)
		package.tags.clear()
		for tag_id in data["tags"]:
			if is_int(tag_id):
				tag = Tag.query.get(tag_id)
			else:
				tag = Tag.query.filter_by(name=tag_id).first()
				if tag is None:
					raise LogicError(400, "Unknown tag: " + tag_id)

			if not was_web and tag.is_protected:
				break

			if tag.is_protected and tag not in old_tags and not user.rank.atLeast(UserRank.EDITOR):
				raise LogicError(400, f"Unable to add protected tag {tag.title} to package")

			package.tags.append(tag)

		if not was_web:
			for tag in old_tags:
				if tag.is_protected:
					package.tags.append(tag)

	if "content_warnings" in data:
		package.content_warnings.clear()
		for warning_id in data["content_warnings"]:
			if is_int(warning_id):
				package.content_warnings.append(ContentWarning.query.get(warning_id))
			else:
				warning = ContentWarning.query.filter_by(name=warning_id).first()
				if warning is None:
					raise LogicError(400, "Unknown warning: " + warning_id)
				package.content_warnings.append(warning)

	if not was_new:
		if reason is None:
			msg = "Edited {}".format(package.title)
		else:
			msg = "Edited {} ({})".format(package.title, reason)

		severity = AuditSeverity.NORMAL if user in package.maintainers else AuditSeverity.EDITOR
		addAuditLog(severity, user, msg, package.getURL("packages.view"), package)

	db.session.commit()

	return package
