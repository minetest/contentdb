# ContentDB
# Copyright (C) 2018  rubenwardy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import os, git, tempfile, shutil, gitdb, contextlib
from git import GitCommandError
from git_archive_all import GitArchiver
from urllib.error import HTTPError
import urllib.request
from urllib.parse import urlsplit
from zipfile import ZipFile

from kombu import uuid

from app.models import *
from app.tasks import celery, TaskError
from app.utils import randomString, getExtension, post_bot_message
from .minetestcheck import build_tree, MinetestCheckError, ContentType


def generateGitURL(urlstr):
	scheme, netloc, path, query, frag = urlsplit(urlstr)

	return "http://:@" + netloc + path + query


@contextlib.contextmanager
def get_temp_dir():
	temp = os.path.join(tempfile.gettempdir(), randomString(10))
	yield temp
	shutil.rmtree(temp)


# Clones a repo from an unvalidated URL.
# Returns a tuple of path and repo on sucess.
# Throws `TaskError` on failure.
# Caller is responsible for deleting returned directory.
@contextlib.contextmanager
def clone_repo(urlstr, ref=None, recursive=False):
	gitDir = os.path.join(tempfile.gettempdir(), randomString(10))

	err = None
	try:
		gitUrl = generateGitURL(urlstr)
		print("Cloning from " + gitUrl)

		if ref is None:
			repo = git.Repo.clone_from(gitUrl, gitDir,
					progress=None, env=None, depth=1, recursive=recursive, kill_after_timeout=15)
		else:
			assert ref != ""

			repo = git.Repo.init(gitDir)
			origin = repo.create_remote("origin", url=gitUrl)
			assert origin.exists()
			origin.fetch()
			repo.git.checkout(ref)

			for submodule in repo.submodules:
				submodule.update(init=True)

		yield repo
		shutil.rmtree(gitDir)
		return

	except GitCommandError as e:
		# This is needed to stop the backtrace being weird
		err = e.stderr

	except gitdb.exc.BadName as e:
		err = "Unable to find the reference " + (ref or "?") + "\n" + e.stderr

	raise TaskError(err.replace("stderr: ", "") \
			.replace("Cloning into '" + gitDir + "'...", "") \
			.strip())


def get_commit_hash(urlstr, ref_name=None):
	gitDir = os.path.join(tempfile.gettempdir(), randomString(10))
	gitUrl = generateGitURL(urlstr)
	assert ref_name != ""

	repo = git.Repo.init(gitDir)
	origin: git.Remote = repo.create_remote("origin", url=gitUrl)
	assert origin.exists()
	origin.fetch()

	if ref_name:
		ref: git.Reference = origin.refs[ref_name]
	else:
		ref: git.Reference = origin.refs[0]

	return ref.commit.hexsha


@celery.task()
def getMeta(urlstr, author):
	with clone_repo(urlstr, recursive=True) as repo:
		try:
			tree = build_tree(repo.working_tree_dir, author=author, repo=urlstr)
		except MinetestCheckError as err:
			raise TaskError(str(err))

		result = {"name": tree.name, "provides": tree.getModNames(), "type": tree.type.name}

		for key in ["depends", "optional_depends"]:
			result[key] = tree.fold("meta", key)

		for key in ["title", "repo", "issueTracker", "forumId", "description", "short_description"]:
			result[key] = tree.get(key)

		for mod in result["provides"]:
			result["depends"].discard(mod)
			result["optional_depends"].discard(mod)

		for key, value in result.items():
			if isinstance(value, set):
				result[key] = list(value)

		return result


def postReleaseCheckUpdate(self, release, path):
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

		return tree

	except MinetestCheckError as err:
		db.session.rollback()

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


@celery.task(bind=True)
def importForeignDownloads(self, id):
	release = PackageRelease.query.get(id)
	if release is None:
		raise TaskError("No such release!")
	elif release.package is None:
		raise TaskError("No package attached to release")
	elif not release.url.startswith("http"):
		return

	try:
		ext = getExtension(release.url)
		filename = randomString(10) + "." + ext
		filepath = os.path.join(app.config["UPLOAD_DIR"], filename)
		urllib.request.urlretrieve(release.url, filepath)

		release.url = "/uploads/" + filename
		db.session.commit()

	except urllib.error.URLError:
		db.session.rollback()
		release.task_id = self.request.id
		release.approved = False
		db.session.commit()


@celery.task(bind=True)
def check_update_config(self, package_id):
	package: Package = Package.query.get(package_id)
	if package is None:
		raise TaskError("No such package!")
	elif package.update_config is None:
		raise TaskError("No update config attached to package")

	config = package.update_config

	if config.trigger != PackageUpdateTrigger.COMMIT:
		return

	err = None
	try:
		hash = get_commit_hash(package.repo, package.update_config.ref)
	except IndexError as e:
		err = "Unable to find the reference.\n" + str(e)
	except GitCommandError as e:
		# This is needed to stop the backtrace being weird
		err = e.stderr
	except gitdb.exc.BadName as e:
		err = "Unable to find the reference " + (package.update_config.ref or "?") + "\n" + e.stderr

	if err:
		err = err.replace("stderr: ", "") \
			.replace("Cloning into '/tmp/", "Cloning into '") \
			.strip()

		msg = "Error: {}.\n\nTask ID: {}\n\n[Change update configuration]({})" \
				.format(err, self.request.id, package.getUpdateConfigURL())

		post_bot_message(package, "Failed to check git repository", msg)

		db.session.commit()
		return

	if config.last_commit == hash:
		return

	if not config.last_commit:
		config.last_commit = hash
		db.session.commit()
		return

	if config.make_release:
		rel = PackageRelease()
		rel.package = package
		rel.title = hash[0:5]
		rel.url = ""
		rel.task_id = uuid()
		db.session.add(rel)
		db.session.commit()

		makeVCSRelease.apply_async((rel.id, package.update_config.ref), task_id=rel.task_id)

	elif not config.outdated:
		config.outdated = True

		msg_last = ""
		if config.last_commit:
			msg_last = " The last commit was {}".format(config.last_commit[0:5])

		msg = "New commit {} was found on the Git repository.{}\n\n[Change update configuration]({})" \
			.format(hash[0:5], msg_last, package.getUpdateConfigURL())

		post_bot_message(package, "New commit detected, package may be outdated", msg)

	config.last_commit = hash
	db.session.commit()


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
