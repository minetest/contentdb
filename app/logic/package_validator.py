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

	if package.releases.filter(PackageRelease.task_id.is_(None)).count() == 0:
		retval.append(("danger", lazy_gettext("A release is required before this package can be approved.")))
		# Don't bother validating any more until we have a release
		return retval

	missing_deps = package.getMissingHardDependenciesQuery().all()
	if len(missing_deps) > 0:
		retval.append(("danger", lazy_gettext(
			"The following hard dependencies need to be added to ContentDB first: %(deps)s", deps=missing_deps)))

	if (package.type == package.type.GAME or package.type == package.type.TXP) and \
		package.screenshots.count() == 0:
		retval.append(("danger", lazy_gettext("You need to add at least one screenshot.")))

	if "Other" in package.license.name or "Other" in package.media_license.name:
		retval.append(("info", lazy_gettext("Please wait for the license to be added to CDB.")))

	return retval
