# ContentDB
# Copyright (C) 2018-21  rubenwardy
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
import json
import os, shutil, gitdb
from zipfile import ZipFile
from git import GitCommandError
from git_archive_all import GitArchiver
from kombu import uuid

from app.models import *
from app.tasks import celery, TaskError
from app.utils import randomString, post_bot_message, addSystemNotification, addSystemAuditLog, get_system_user
from app.utils.git import clone_repo, get_latest_tag, get_latest_commit, get_temp_dir
from .minetestcheck import build_tree, MinetestCheckError, ContentType
from ..logic.LogicError import LogicError
from ..logic.packages import do_edit_package, ALIASES


@celery.task()
def getMeta(urlstr, author):
	with clone_repo(urlstr, recursive=True) as repo:
		try:
			tree = build_tree(repo.working_tree_dir, author=author, repo=urlstr)
		except MinetestCheckError as err:
			raise TaskError(str(err))

		result = {"name": tree.name, "type": tree.type.name}

		for key in ["title", "repo", "issueTracker", "forumId", "description", "short_description"]:
			result[key] = tree.get(key)

		result["forums"] = result.get("forumId")

		readme_path = tree.getReadMePath()
		if readme_path:
			with open(readme_path, "r") as f:
				result["long_description"] = f.read()

		try:
			with open(os.path.join(tree.baseDir, ".cdb.json"), "r") as f:
				data = json.loads(f.read())
				for key, value in data.items():
					result[key] = value
		except LogicError as e:
			raise TaskError(e.message)
		except IOError:
			pass

		for alias, to in ALIASES.items():
			if alias in result:
				result[to] = result[alias]

		for key, value in result.items():
			if isinstance(value, set):
				result[key] = list(value)

		return result


def get_edit_data_from_dir(dir: str):
	data = {}
	for path in [os.path.join(dir, ".cdb.json"), os.path.join(dir, ".cdb", "meta.json")]:
		if os.path.isfile(path):
			with open(path, "r") as f:
				data = json.loads(f.read())
			break

	for path in [os.path.join(dir, ".cdb.md"), os.path.join(dir, ".cdb", "long_description.md")]:
		if os.path.isfile(path):
			with open(path, "r") as f:
				data["long_description"] = f.read().replace("\r\n", "\n")
			break

	return data


def postReleaseCheckUpdate(self, release: PackageRelease, path):
	try:
		tree = build_tree(path, expected_type=ContentType[release.package.type.name],
				author=release.package.author.username, name=release.package.name)

		cache = {}
		def getMetaPackages(names):
			return [ MetaPackage.GetOrCreate(x, cache) for x in names ]

		provides = tree.getModNames()

		package = release.package
		package.provides.clear()
		package.provides.extend(getMetaPackages(tree.getModNames()))

		# Delete all meta package dependencies
		package.dependencies.filter(Dependency.meta_package != None).delete()

		# Get raw dependencies
		depends = tree.fold("meta", "depends")
		optional_depends = tree.fold("meta", "optional_depends")

		# Filter out provides
		for mod in provides:
			depends.discard(mod)
			optional_depends.discard(mod)

		# Raise error on unresolved game dependencies
		if package.type == PackageType.GAME and len(depends) > 0:
			deps = ", ".join(depends)
			raise MinetestCheckError("Game has unresolved hard dependencies: " + deps)

		# Add dependencies
		for meta in getMetaPackages(depends):
			db.session.add(Dependency(package, meta=meta, optional=False))

		for meta in getMetaPackages(optional_depends):
			db.session.add(Dependency(package, meta=meta, optional=True))

		# Update min/max
		if tree.meta.get("min_minetest_version"):
			release.min_rel = MinetestRelease.get(tree.meta["min_minetest_version"], None)

		if tree.meta.get("max_minetest_version"):
			release.max_rel = MinetestRelease.get(tree.meta["max_minetest_version"], None)

		try:
			data = get_edit_data_from_dir(tree.baseDir)
			if data != {}:  # Not sure if this will actually work to check not empty, probably not
				do_edit_package(package.author, package, False, data, "Post release hook")
		except LogicError as e:
			raise TaskError(e.message)

		return tree

	except MinetestCheckError as err:
		db.session.rollback()

		msg = f"{err}\n\nTask ID: {self.request.id}\n\nRelease: [View Release]({release.getEditURL()})"
		post_bot_message(release.package, f"Release {release.title} validation failed", msg)

		if "Fails validation" not in release.title:
			release.title += " (Fails validation)"

		release.task_id = self.request.id
		release.approved = False
		db.session.commit()

		raise TaskError(str(err))


@celery.task(bind=True)
def checkZipRelease(self, id, path):
	release = PackageRelease.query.get(id)
	if release is None:
		raise TaskError("No such release!")
	elif release.package is None:
		raise TaskError("No package attached to release")

	with get_temp_dir() as temp:
		with ZipFile(path, 'r') as zip_ref:
			zip_ref.extractall(temp)

		postReleaseCheckUpdate(self, release, temp)

		release.task_id = None
		release.approve(release.package.author)
		db.session.commit()


@celery.task(bind=True)
def makeVCSRelease(self, id, branch):
	release = PackageRelease.query.get(id)
	if release is None:
		raise TaskError("No such release!")
	elif release.package is None:
		raise TaskError("No package attached to release")

	with clone_repo(release.package.repo, ref=branch, recursive=True) as repo:
		postReleaseCheckUpdate(self, release, repo.working_tree_dir)

		filename = randomString(10) + ".zip"
		destPath = os.path.join(app.config["UPLOAD_DIR"], filename)

		assert(not os.path.isfile(destPath))
		archiver = GitArchiver(prefix=release.package.name, force_sub=True, main_repo_abspath=repo.working_tree_dir)
		archiver.create(destPath)
		assert(os.path.isfile(destPath))

		release.url         = "/uploads/" + filename
		release.task_id     = None
		release.commit_hash = repo.head.object.hexsha
		release.approve(release.package.author)
		db.session.commit()

		return release.url


@celery.task()
def importRepoScreenshot(id):
	package = Package.query.get(id)
	if package is None or package.state == PackageState.DELETED:
		raise Exception("Unexpected none package")

	try:
		with clone_repo(package.repo) as repo:
			for ext in ["png", "jpg", "jpeg"]:
				sourcePath = repo.working_tree_dir + "/screenshot." + ext
				if os.path.isfile(sourcePath):
					filename = randomString(10) + "." + ext
					destPath = os.path.join(app.config["UPLOAD_DIR"], filename)
					shutil.copyfile(sourcePath, destPath)

					ss = PackageScreenshot()
					ss.approved = True
					ss.package = package
					ss.title   = "screenshot.png"
					ss.url	 = "/uploads/" + filename
					db.session.add(ss)
					db.session.commit()

					return "/uploads/" + filename

	except TaskError as e:
		# ignore download errors
		print(e)
		pass

	print("screenshot.png does not exist")
	return None


def check_update_config_impl(package):
	config = package.update_config

	if config.trigger == PackageUpdateTrigger.COMMIT:
		tag = None
		commit = get_latest_commit(package.repo, package.update_config.ref)
	elif config.trigger == PackageUpdateTrigger.TAG:
		tag, commit = get_latest_tag(package.repo)
	else:
		raise TaskError("Unknown update trigger")

	if commit is None:
		return

	if config.last_commit == commit:
		if tag and config.last_tag != tag:
			config.last_tag = tag
			db.session.commit()
		return

	if not config.last_commit:
		config.last_commit = commit
		config.last_tag = tag
		db.session.commit()
		return

	if package.releases.filter_by(commit_hash=commit).count() > 0:
		return

	if config.make_release:
		rel = PackageRelease()
		rel.package = package
		rel.title = tag if tag else datetime.datetime.utcnow().strftime("%Y-%m-%d")
		rel.url = ""
		rel.task_id = uuid()
		db.session.add(rel)

		msg = "Created release {} (Git Update Detection)".format(rel.title)
		addSystemAuditLog(AuditSeverity.NORMAL, msg, package.getDetailsURL(), package)

		db.session.commit()

		makeVCSRelease.apply_async((rel.id, commit), task_id=rel.task_id)

	elif config.outdated_at is None:
		config.set_outdated()

		if config.trigger == PackageUpdateTrigger.COMMIT:
			msg_last = ""
			if config.last_commit:
				msg_last = " The last commit was {}".format(config.last_commit[0:5])

			msg = "New commit {} found on the Git repo, is the package outdated?{}" \
				.format(commit[0:5], msg_last)
		else:
			msg_last = ""
			if config.last_tag:
				msg_last = " The last tag was {}".format(config.last_tag)

			msg = "New tag {} found on the Git repo.{}" \
				.format(tag, msg_last)

		for user in package.maintainers:
			addSystemNotification(user, NotificationType.BOT,
					msg, url_for("todo.view_user", username=user.username, _external=False), package)

	config.last_commit = commit
	config.last_tag = tag
	db.session.commit()


@celery.task(bind=True)
def check_update_config(self, package_id):
	package: Package = Package.query.get(package_id)
	if package is None:
		raise TaskError("No such package!")
	elif package.update_config is None:
		raise TaskError("No update config attached to package")

	err = None
	try:
		check_update_config_impl(package)
	except GitCommandError as e:
		# This is needed to stop the backtrace being weird
		err = e.stderr
	except gitdb.exc.BadName as e:
		err = "Unable to find the reference " + (package.update_config.ref or "?") + "\n" + e.stderr
	except TaskError as e:
		err = e.value

	if err:
		err = err.replace("stderr: ", "") \
			.replace("Cloning into '/tmp/", "Cloning into '") \
			.strip()

		msg = "Error: {}.\n\nTask ID: {}\n\n[Change update configuration]({})" \
			.format(err, self.request.id, package.getUpdateConfigURL())

		post_bot_message(package, "Failed to check git repository", msg)

		db.session.commit()
		return


@celery.task
def check_for_updates():
	for update_config in PackageUpdateConfig.query.all():
		update_config: PackageUpdateConfig

		if not update_config.package.approved:
			continue

		if update_config.package.repo is None:
			db.session.delete(update_config)
			continue

		check_update_config.delay(update_config.package_id)

	db.session.commit()
