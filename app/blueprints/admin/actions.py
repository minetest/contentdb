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
from typing import List

from celery import group
from flask import *
from sqlalchemy import or_

from app.models import *
from app.tasks.forumtasks import importTopicList, checkAllForumAccounts
from app.tasks.importtasks import importRepoScreenshot, checkZipRelease, check_for_updates
from app.utils import addNotification, get_system_user

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
	PackageRelease.query.filter(PackageRelease.task_id != None).delete()
	db.session.commit()
	return redirect(url_for("admin.admin_page"))

@action("Check releases")
def check_releases():
	releases = PackageRelease.query.filter(PackageRelease.url.like("/uploads/%")).all()

	tasks = []
	for release in releases:
		zippath = release.url.replace("/uploads/", app.config["UPLOAD_DIR"])
		tasks.append(checkZipRelease.s(release.id, zippath))

	result = group(tasks).apply_async()

	while not result.ready():
		import time
		time.sleep(0.1)

	return redirect(url_for("todo.view_editor"))

@action("Reimport packages")
def reimport_packages():
	tasks = []
	for package in Package.query.filter(Package.state!=PackageState.DELETED).all():
		release = package.releases.first()
		if release:
			zippath = release.url.replace("/uploads/", app.config["UPLOAD_DIR"])
			tasks.append(checkZipRelease.s(release.id, zippath))

	result = group(tasks).apply_async()

	while not result.ready():
		import time
		time.sleep(0.1)

	return redirect(url_for("todo.view_editor"))

@action("Import topic list")
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
		.filter(Package.state!=PackageState.DELETED) \
		.outerjoin(PackageScreenshot, Package.id==PackageScreenshot.package_id) \
		.filter(PackageScreenshot.id==None) \
		.all()
	for package in packages:
		importRepoScreenshot.delay(package.id)

	return redirect(url_for("admin.admin_page"))

@action("Clean uploads")
def clean_uploads():
	upload_dir = app.config['UPLOAD_DIR']

	(_, _, filenames) = next(os.walk(upload_dir))
	existing_uploads = set(filenames)

	if len(existing_uploads) != 0:
		def getURLsFromDB(column):
			results = db.session.query(column).filter(column != None, column != "").all()
			return set([os.path.basename(x[0]) for x in results])

		release_urls = getURLsFromDB(PackageRelease.url)
		screenshot_urls = getURLsFromDB(PackageScreenshot.url)

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

@action("Delete metapackages")
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

@action("Add update config")
def add_update_config():
	added = 0
	for pkg in Package.query.filter(Package.repo != None, Package.releases.any(), Package.update_config == None).all():
		pkg.update_config = PackageUpdateConfig()
		pkg.update_config.auto_created = True

		release: PackageRelease = pkg.releases.first()
		if release and release.commit_hash:
			pkg.update_config.last_commit = release.commit_hash

		db.session.add(pkg.update_config)
		added += 1

	db.session.commit()

	flash("Added {} update configs".format(added), "success")
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
		packages_list = "and ".join(packages)
	return packages_list

@action("Send WIP package notification")
def remind_wip():
	users = User.query.filter(User.packages.any(or_(Package.state==PackageState.WIP, Package.state==PackageState.CHANGES_NEEDED)))
	system_user = get_system_user()
	for user in users:
		packages = db.session.query(Package.title).filter(
				Package.author_id==user.id,
				or_(Package.state==PackageState.WIP, Package.state==PackageState.CHANGES_NEEDED)) \
			.all()

		packages = [pkg[0] for pkg in packages]
		packages_list = _package_list(packages)
		havent = "haven't" if len(packages) > 1 else "hasn't"
		if len(packages_list) + 54  > 100:
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
