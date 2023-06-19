# ContentDB
# Copyright (C) rubenwardy
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

from collections import namedtuple
from typing import List

from flask_babel import lazy_gettext
from sqlalchemy import and_, or_

from app.models import Package, PackageType, PackageState, PackageRelease

ValidationError = namedtuple("ValidationError", "status message")


def validate_package_for_approval(package: Package) -> List[ValidationError]:
	retval: List[ValidationError] = []

	normalised_name = package.getNormalisedName()
	if package.type != PackageType.MOD and Package.query.filter(
			and_(Package.state == PackageState.APPROVED,
				or_(Package.name == normalised_name,
					Package.name == normalised_name + "_game"))).count() > 0:
		retval.append(("danger", lazy_gettext("A package already exists with this name. Please see Policy and Guidance 3")))

	if package.releases.filter(PackageRelease.task_id == None).count() == 0:
		retval.append(("danger", lazy_gettext("A release is required before this package can be approved.")))
		# Don't bother validating any more until we have a release
		return retval

	missing_deps = package.get_missing_hard_dependencies_query().all()
	if len(missing_deps) > 0:
		retval.append(("danger", lazy_gettext(
			"The following hard dependencies need to be added to ContentDB first: %(deps)s", deps=missing_deps)))

	if (package.type == package.type.GAME or package.type == package.type.TXP) and \
		package.screenshots.count() == 0:
		retval.append(("danger", lazy_gettext("You need to add at least one screenshot.")))

	if "Other" in package.license.name or "Other" in package.media_license.name:
		retval.append(("info", lazy_gettext("Please wait for the license to be added to CDB.")))

	return retval
