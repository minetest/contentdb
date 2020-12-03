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


import flask, json, os, git, tempfile, shutil, gitdb, contextlib
from git import GitCommandError
from git_archive_all import GitArchiver
from flask_sqlalchemy import SQLAlchemy
from urllib.error import HTTPError
import urllib.request
from urllib.parse import urlparse, quote_plus, urlsplit
from zipfile import ZipFile

from app import app
from app.models import *
from app.tasks import celery, TaskError
from app.utils import randomString, getExtension
from .minetestcheck import build_tree, MinetestCheckError, ContentType
from .minetestcheck.config import parse_conf
from .krocklist import getKrockList, findModInfo


def generateGitURL(urlstr):
	scheme, netloc, path, query, frag = urlsplit(urlstr)

	return "http://:@" + netloc + path + query


@contextlib.contextmanager
def getTempDir():
	temp = os.path.join(tempfile.gettempdir(), randomString(10))
	yield temp
	shutil.rmtree(temp)


# Clones a repo from an unvalidated URL.
# Returns a tuple of path and repo on sucess.
# Throws `TaskError` on failure.
# Caller is responsible for deleting returned directory.
@contextlib.contextmanager
def cloneRepo(urlstr, ref=None, recursive=False):
	gitDir = os.path.join(tempfile.gettempdir(), randomString(10))

	err = None
	try:
		gitUrl = generateGitURL(urlstr)
		print("Cloning from " + gitUrl)

		if ref is None:
			repo = git.Repo.clone_from(gitUrl, gitDir, \
					progress=None, env=None, depth=1, recursive=recursive, kill_after_timeout=15)
		else:
			repo = git.Repo.init(gitDir)
			origin = repo.create_remote("origin", url=gitUrl)
			assert origin.exists()
			origin.fetch()
			origin.pull(ref)

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


@celery.task()
def getMeta(urlstr, author):
	with cloneRepo(urlstr, recursive=True) as repo:
		try:
			tree = build_tree(repo.working_tree_dir, author=author, repo=urlstr)
		except MinetestCheckError as err:
			raise TaskError(str(err))

		result = {}
		result["name"] = tree.name
		result["provides"] = tree.getModNames()
		result["type"] = tree.type.name

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
		tree = build_tree(path, expected_type=ContentType[release.package.type.name], \
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
def updateMetaFromRelease(self, id, path):
	release = PackageRelease.query.get(id)
	if release is None:
		raise TaskError("No such release!")
	elif release.package is None:
		raise TaskError("No package attached to release")

	print("updateMetaFromRelease: {} for {}/{}" \
		.format(id, release.package.author.display_name, release.package.name))

	with getTempDir() as temp:
		with ZipFile(path, 'r') as zip_ref:
			zip_ref.extractall(temp)

		postReleaseCheckUpdate(self, release, temp)
		db.session.commit()


@celery.task(bind=True)
def checkZipRelease(self, id, path):
	release = PackageRelease.query.get(id)
	if release is None:
		raise TaskError("No such release!")
	elif release.package is None:
		raise TaskError("No package attached to release")

	with getTempDir() as temp:
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

	with cloneRepo(release.package.repo, ref=branch, recursive=True) as repo:
		postReleaseCheckUpdate(self, release, repo.working_tree_dir)

		filename = randomString(10) + ".zip"
		destPath = os.path.join(app.config["UPLOAD_DIR"], filename)

		assert(not os.path.isfile(destPath))
		archiver = GitArchiver(force_sub=True, main_repo_abspath=repo.working_tree_dir)
		archiver.create(destPath)
		assert(os.path.isfile(destPath))

		release.url         = "/uploads/" + filename
		release.task_id     = None
		release.commit_hash = repo.head.object.hexsha
		release.approve(release.package.author)
		db.session.commit()

		updateMetaFromRelease.delay(release.id, destPath)

		return release.url


@celery.task()
def importRepoScreenshot(id):
	package = Package.query.get(id)
	if package is None or package.state == PackageState.DELETED:
		raise Exception("Unexpected none package")

	try:
		with cloneRepo(package.repo) as repo:
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
