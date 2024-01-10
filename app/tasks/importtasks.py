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

import datetime
import json
import os
import shutil
from json import JSONDecodeError
from zipfile import ZipFile

import gitdb
from flask import url_for
from git import GitCommandError
from git_archive_all import GitArchiver
from kombu import uuid
from sqlalchemy import and_

from app.models import AuditSeverity, db, NotificationType, PackageRelease, MetaPackage, Dependency, PackageType, \
	MinetestRelease, Package, PackageState, PackageScreenshot, PackageUpdateTrigger, PackageUpdateConfig, \
	PackageGameSupport
from app.tasks import celery, TaskError
from app.utils import random_string, post_bot_message, add_system_notification, add_system_audit_log, \
	get_games_from_list
from app.utils.git import clone_repo, get_latest_tag, get_latest_commit, get_temp_dir
from .minetestcheck import build_tree, MinetestCheckError, ContentType
from app import app
from app.logic.LogicError import LogicError
from app.logic.game_support import GameSupportResolver
from app.logic.packages import do_edit_package, ALIASES
from app.utils.image import get_image_size


@celery.task()
def get_meta(urlstr, author):
	with clone_repo(urlstr, recursive=True) as repo:
		try:
			tree = build_tree(repo.working_tree_dir, author=author, repo=urlstr)
		except MinetestCheckError as err:
			raise TaskError(str(err))

		result = {"name": tree.name, "type": tree.type.name}

		for key in ["title", "repo", "issueTracker", "forumId", "description", "short_description"]:
			result[key] = tree.get(key)

		result["forums"] = result.get("forumId")

		readme_path = tree.get_readme_path()
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
		except JSONDecodeError as e:
			raise TaskError("Whilst reading .cdb.json: " + str(e))
		except IOError:
			pass

		for alias, to in ALIASES.items():
			if alias in result:
				result[to] = result[alias]

		for key, value in result.items():
			if isinstance(value, set):
				result[key] = list(value)

		return result


@celery.task()
def update_all_game_support():
	resolver = GameSupportResolver(db.session)
	resolver.init_all()
	db.session.commit()


def post_release_check_update(self, release: PackageRelease, path):
	try:
		tree = build_tree(path, expected_type=ContentType[release.package.type.name],
				author=release.package.author.username, name=release.package.name)

		if tree.name is not None and release.package.name != tree.name and tree.type == ContentType.MOD:
			raise MinetestCheckError(f"Expected {tree.relative} to have technical name {release.package.name}, instead has name {tree.name}")

		cache = {}
		def get_meta_packages(names):
			return [ MetaPackage.GetOrCreate(x, cache) for x in names ]

		provides = tree.get_mod_names()

		package = release.package
		package.provides.clear()
		package.provides.extend(get_meta_packages(tree.get_mod_names()))

		# Delete all mod name dependencies
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

		if package.state != PackageState.APPROVED and tree.find_license_file() is None:
			raise MinetestCheckError(
				"You need to add a LICENSE.txt/.md or COPYING file to your package. See the 'Copyright Guide' for more info")

		# Add dependencies
		for meta in get_meta_packages(depends):
			db.session.add(Dependency(package, meta=meta, optional=False))

		for meta in get_meta_packages(optional_depends):
			db.session.add(Dependency(package, meta=meta, optional=True))

		# Update min/max
		if tree.meta.get("min_minetest_version"):
			release.min_rel = MinetestRelease.get(tree.meta["min_minetest_version"], None)

		if tree.meta.get("max_minetest_version"):
			release.max_rel = MinetestRelease.get(tree.meta["max_minetest_version"], None)

		try:
			with open(os.path.join(tree.baseDir, ".cdb.json"), "r") as f:
				data = json.loads(f.read())
				do_edit_package(package.author, package, False, False, data, "Post release hook")
		except LogicError as e:
			raise TaskError(e.message)
		except JSONDecodeError as e:
			raise TaskError("Whilst reading .cdb.json: " + str(e))
		except IOError:
			pass

		# Update game support
		if package.type == PackageType.MOD or package.type == PackageType.TXP:
			try:
				resolver = GameSupportResolver(db.session)

				game_is_supported = {}
				if "supported_games" in tree.meta:
					for game in get_games_from_list(db.session, tree.meta["supported_games"]):
						game_is_supported[game.id] = True

					has_star = any(map(lambda x: x.strip() == "*", tree.meta["supported_games"]))
					if has_star:
						if package.type == PackageType.TXP or \
							package.supported_games.filter(and_(
								PackageGameSupport.confidence == 1, PackageGameSupport.supports == True)).count() > 0:
							raise TaskError("The package depends on a game-specific mod, and so cannot support all games.")

						package.supports_all_games = True
				if "unsupported_games" in tree.meta:
					for game in get_games_from_list(db.session, tree.meta["unsupported_games"]):
						game_is_supported[game.id] = False

				resolver.set_supported(package, game_is_supported, 10)
				if package.type == PackageType.MOD:
					resolver.update(package)
			except LogicError as e:
				raise TaskError(e.message)

		return tree

	except MinetestCheckError as err:
		db.session.rollback()

		task_url = url_for('tasks.check', id=self.request.id)
		msg = f"{err}\n\n[View Release]({release.get_edit_url()}) | [View Task]({task_url})"
		post_bot_message(release.package, f"Release {release.title} validation failed", msg)

		if "Fails validation" not in release.title:
			release.title += " (Fails validation)"

		release.task_id = self.request.id
		release.approved = False
		db.session.commit()

		raise TaskError(str(err))


@celery.task(bind=True)
def check_zip_release(self, id, path):
	release = PackageRelease.query.get(id)
	if release is None:
		raise TaskError("No such release!")
	elif release.package is None:
		raise TaskError("No package attached to release")

	with get_temp_dir() as temp:
		with ZipFile(path, 'r') as zip_ref:
			zip_ref.extractall(temp)

		post_release_check_update(self, release, temp)

		release.task_id = None
		release.approve(release.package.author)
		db.session.commit()


@celery.task(bind=True)
def make_vcs_release(self, id, branch):
	release = PackageRelease.query.get(id)
	if release is None:
		raise TaskError("No such release!")
	elif release.package is None:
		raise TaskError("No package attached to release")

	with clone_repo(release.package.repo, ref=branch, recursive=True) as repo:
		post_release_check_update(self, release, repo.working_tree_dir)

		filename = random_string(10) + ".zip"
		dest_path = os.path.join(app.config["UPLOAD_DIR"], filename)

		assert not os.path.isfile(dest_path)
		archiver = GitArchiver(prefix=release.package.name, force_sub=True, main_repo_abspath=repo.working_tree_dir)
		archiver.create(dest_path)
		assert os.path.isfile(dest_path)

		file_stats = os.stat(dest_path)
		if file_stats.st_size / (1024 * 1024) > 100:
			os.remove(dest_path)
			raise TaskError("The .zip file created from Git is too large - needs to be less than 100MB")

		release.url         = "/uploads/" + filename
		release.task_id     = None
		release.commit_hash = repo.head.object.hexsha
		release.approve(release.package.author)
		db.session.commit()

		return release.url


@celery.task()
def import_repo_screenshot(id):
	package = Package.query.get(id)
	if package is None or package.state == PackageState.DELETED:
		raise Exception("Unexpected none package")

	try:
		with clone_repo(package.repo) as repo:
			for ext in ["png", "jpg", "jpeg"]:
				sourcePath = repo.working_tree_dir + "/screenshot." + ext
				if os.path.isfile(sourcePath):
					filename = random_string(10) + "." + ext
					destPath = os.path.join(app.config["UPLOAD_DIR"], filename)
					shutil.copyfile(sourcePath, destPath)

					ss = PackageScreenshot()
					ss.approved = True
					ss.package = package
					ss.title   = "screenshot.png"
					ss.url	 = "/uploads/" + filename
					ss.width, ss.height = get_image_size(destPath)
					if ss.is_too_small():
						return None

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
		add_system_audit_log(AuditSeverity.NORMAL, msg, package.get_url("packages.view"), package)

		db.session.commit()

		make_vcs_release.apply_async((rel.id, commit), task_id=rel.task_id)

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
			add_system_notification(user, NotificationType.BOT,
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

		msg = "Error: {}.\n\n[Change update configuration]({}) | [View task]({})" \
			.format(err, package.get_url("packages.update_config"), url_for("tasks.check", id=self.request.id))

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
