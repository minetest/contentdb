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


import os
import sys
from typing import List

import requests
from celery import group
from flask import redirect, url_for, flash, current_app, jsonify
from sqlalchemy import or_, and_

from app.logic.game_support import GameSupportResolver
from app.models import PackageRelease, db, Package, PackageState, PackageScreenshot, MetaPackage, User, \
	NotificationType, PackageUpdateConfig, License, UserRank, PackageType, PackageGameSupport
from app.tasks.forumtasks import importTopicList, checkAllForumAccounts
from app.tasks.importtasks import importRepoScreenshot, checkZipRelease, check_for_updates
from app.utils import addNotification, get_system_user
from app.utils.image import get_image_size

actions = {}


def action(title: str):
	def func(f):
		name = f.__name__
		actions[name] = {
			"title": title,
			"func": f,
		}

		return f

	return func


@action("Delete stuck releases")
def del_stuck_releases():
	PackageRelease.query.filter(PackageRelease.task_id.isnot(None)).delete()
	db.session.commit()
	return redirect(url_for("admin.admin_page"))


@action("Check ZIP releases")
def check_releases():
	releases = PackageRelease.query.filter(PackageRelease.url.like("/uploads/%")).all()

	tasks = []
	for release in releases:
		tasks.append(checkZipRelease.s(release.id, release.file_path))

	result = group(tasks).apply_async()

	while not result.ready():
		import time
		time.sleep(0.1)

	return redirect(url_for("todo.view_editor"))


@action("Check the first release of all packages")
def reimport_packages():
	tasks = []
	for package in Package.query.filter(Package.state != PackageState.DELETED).all():
		release = package.releases.first()
		if release:
			tasks.append(checkZipRelease.s(release.id, release.file_path))

	result = group(tasks).apply_async()

	while not result.ready():
		import time
		time.sleep(0.1)

	return redirect(url_for("todo.view_editor"))


@action("Import forum topic list")
def import_topic_list():
	task = importTopicList.delay()
	return redirect(url_for("tasks.check", id=task.id, r=url_for("todo.topics")))


@action("Check all forum accounts")
def check_all_forum_accounts():
	task = checkAllForumAccounts.delay()
	return redirect(url_for("tasks.check", id=task.id, r=url_for("admin.admin_page")))


@action("Import screenshots")
def import_screenshots():
	packages = Package.query \
		.filter(Package.state != PackageState.DELETED) \
		.outerjoin(PackageScreenshot, Package.id == PackageScreenshot.package_id) \
		.filter(PackageScreenshot.id.is_(None)) \
		.all()
	for package in packages:
		importRepoScreenshot.delay(package.id)

	return redirect(url_for("admin.admin_page"))


@action("Remove unused uploads")
def clean_uploads():
	upload_dir = current_app.config['UPLOAD_DIR']

	(_, _, filenames) = next(os.walk(upload_dir))
	existing_uploads = set(filenames)

	if len(existing_uploads) != 0:
		def get_filenames_from_column(column):
			results = db.session.query(column).filter(column.isnot(None), column != "").all()
			return set([os.path.basename(x[0]) for x in results])

		release_urls = get_filenames_from_column(PackageRelease.url)
		screenshot_urls = get_filenames_from_column(PackageScreenshot.url)

		db_urls = release_urls.union(screenshot_urls)
		unreachable = existing_uploads.difference(db_urls)

		import sys
		print("On Disk: ", existing_uploads, file=sys.stderr)
		print("In DB: ", db_urls, file=sys.stderr)
		print("Unreachable: ", unreachable, file=sys.stderr)

		for filename in unreachable:
			os.remove(os.path.join(upload_dir, filename))

		flash("Deleted " + str(len(unreachable)) + " unreachable uploads", "success")
	else:
		flash("No downloads to create", "danger")

	return redirect(url_for("admin.admin_page"))


@action("Delete unused metapackages")
def del_meta_packages():
	query = MetaPackage.query.filter(~MetaPackage.dependencies.any(), ~MetaPackage.packages.any())
	count = query.count()
	query.delete(synchronize_session=False)
	db.session.commit()

	flash("Deleted " + str(count) + " unused meta packages", "success")
	return redirect(url_for("admin.admin_page"))


@action("Delete removed packages")
def del_removed_packages():
	query = Package.query.filter_by(state=PackageState.DELETED)
	count = query.count()
	for pkg in query.all():
		pkg.review_thread = None
		db.session.delete(pkg)
	db.session.commit()

	flash("Deleted {} soft deleted packages packages".format(count), "success")
	return redirect(url_for("admin.admin_page"))


@action("Run update configs")
def run_update_config():
	check_for_updates.delay()

	flash("Started update configs", "success")
	return redirect(url_for("admin.admin_page"))


def _package_list(packages: List[str]):
	# Who needs translations?
	if len(packages) >= 3:
		packages[len(packages) - 1] = "and " + packages[len(packages) - 1]
		packages_list = ", ".join(packages)
	else:
		packages_list = " and ".join(packages)
	return packages_list


@action("Send WIP package notification")
def remind_wip():
	users = User.query.filter(User.packages.any(or_(Package.state == PackageState.WIP, Package.state == PackageState.CHANGES_NEEDED)))
	system_user = get_system_user()
	for user in users:
		packages = db.session.query(Package.title).filter(
				Package.author_id == user.id,
				or_(Package.state == PackageState.WIP, Package.state==PackageState.CHANGES_NEEDED)) \
			.all()

		packages = [pkg[0] for pkg in packages]
		packages_list = _package_list(packages)
		havent = "haven't" if len(packages) > 1 else "hasn't"
		if len(packages_list) + 54 > 100:
			packages_list = packages_list[0:(100-54-1)] + "…"

		addNotification(user, system_user, NotificationType.PACKAGE_APPROVAL,
			f"Did you forget? {packages_list} {havent} been submitted for review yet",
				url_for('todo.view_user', username=user.username))
	db.session.commit()


@action("Send outdated package notification")
def remind_outdated():
	users = User.query.filter(User.maintained_packages.any(
			Package.update_config.has(PackageUpdateConfig.outdated_at.isnot(None))))
	system_user = get_system_user()
	for user in users:
		packages = db.session.query(Package.title).filter(
				Package.maintainers.any(User.id==user.id),
				Package.update_config.has(PackageUpdateConfig.outdated_at.isnot(None))) \
			.all()

		packages = [pkg[0] for pkg in packages]
		packages_list = _package_list(packages)

		addNotification(user, system_user, NotificationType.PACKAGE_APPROVAL,
				f"The following packages may be outdated: {packages_list}",
				url_for('todo.view_user', username=user.username))

	db.session.commit()


@action("Import licenses from SPDX")
def import_licenses():
	renames = {
		"GPLv2": "GPL-2.0-only",
		"GPLv3": "GPL-3.0-only",
		"AGPLv2": "AGPL-2.0-only",
		"AGPLv3": "AGPL-3.0-only",
		"LGPLv2.1": "LGPL-2.1-only",
		"LGPLv3": "LGPL-3.0-only",
		"Apache 2.0": "Apache-2.0",
		"BSD 2-Clause / FreeBSD": "BSD-2-Clause-FreeBSD",
		"BSD 3-Clause": "BSD-3-Clause",
		"CC0": "CC0-1.0",
		"CC BY 3.0": "CC-BY-3.0",
		"CC BY 4.0": "CC-BY-4.0",
		"CC BY-NC-SA 3.0": "CC-BY-NC-SA-3.0",
		"CC BY-SA 3.0": "CC-BY-SA-3.0",
		"CC BY-SA 4.0": "CC-BY-SA-4.0",
		"NPOSLv3": "NPOSL-3.0",
		"MPL 2.0": "MPL-2.0",
		"EUPLv1.2": "EUPL-1.2",
		"SIL Open Font License v1.1": "OFL-1.1",
	}

	for old_name, new_name in renames.items():
		License.query.filter_by(name=old_name).update({ "name": new_name })

	r = requests.get(
			"https://raw.githubusercontent.com/spdx/license-list-data/master/json/licenses.json")
	licenses = r.json()["licenses"]

	existing_licenses = {}
	for license in License.query.all():
		assert license.name not in renames.keys()
		existing_licenses[license.name.lower()] = license

	for license in licenses:
		obj = existing_licenses.get(license["licenseId"].lower())
		if obj:
			obj.url = license["reference"]
		elif license.get("isOsiApproved") and license.get("isFsfLibre") and \
				not license["isDeprecatedLicenseId"]:
			obj = License(license["licenseId"], True, license["reference"])
			db.session.add(obj)

	db.session.commit()


@action("Delete inactive users")
def delete_inactive_users():
	users = User.query.filter(User.is_active == False, User.packages.is_(None), User.forum_topics.is_(None),
			User.rank == UserRank.NOT_JOINED).all()
	for user in users:
		db.session.delete(user)
	db.session.commit()


@action("Send Video URL notification")
def remind_video_url():
	users = User.query.filter(User.maintained_packages.any(
			and_(Package.video_url.is_(None), Package.type==PackageType.GAME, Package.state==PackageState.APPROVED)))
	system_user = get_system_user()
	for user in users:
		packages = db.session.query(Package.title).filter(
				or_(Package.author==user, Package.maintainers.any(User.id==user.id)),
				Package.video_url.is_(None),
				Package.type == PackageType.GAME,
				Package.state == PackageState.APPROVED) \
			.all()

		packages = [pkg[0] for pkg in packages]
		packages_list = _package_list(packages)

		addNotification(user, system_user, NotificationType.PACKAGE_APPROVAL,
				f"You should add a video to {packages_list}",
				url_for('users.profile', username=user.username))

	db.session.commit()


@action("Update screenshot sizes")
def update_screenshot_sizes():
	import sys

	for screenshot in PackageScreenshot.query.all():
		width, height = get_image_size(screenshot.file_path)
		print(f"{screenshot.url}: {width}, {height}", file=sys.stderr)
		screenshot.width = width
		screenshot.height = height

	db.session.commit()


@action("Detect game support")
def detect_game_support():
	resolver = GameSupportResolver()
	resolver.update_all()
	db.session.commit()
