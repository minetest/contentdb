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


import flask, json, os, git, tempfile, shutil, gitdb
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

krock_list_cache = None
krock_list_cache_by_name = None
def getKrockList():
	global krock_list_cache
	global krock_list_cache_by_name

	if krock_list_cache is None:
		contents = urllib.request.urlopen("https://krock-works.uk.to/minetest/modList.php").read().decode("utf-8")
		list = json.loads(contents)

		def h(x):
			if not ("title"   in x and "author" in x and \
					"topicId" in x and "link"   in x and x["link"] != ""):
				return False

			import re
			m = re.search("\[([A-Za-z0-9_]+)\]", x["title"])
			if m is None:
				return False

			x["name"] = m.group(1)
			return True

		def g(x):
			return {
				"title":   x["title"],
				"author":  x["author"],
				"name":	x["name"],
				"topicId": x["topicId"],
				"link":	x["link"],
			}

		krock_list_cache = [g(x) for x in list if h(x)]
		krock_list_cache_by_name = {}
		for x in krock_list_cache:
			if not x["name"] in krock_list_cache_by_name:
				krock_list_cache_by_name[x["name"]] = []

			krock_list_cache_by_name[x["name"]].append(x)

	return krock_list_cache, krock_list_cache_by_name

def findModInfo(author, name, link):
	list, lookup = getKrockList()

	if name is not None and name in lookup:
		if len(lookup[name]) == 1:
			return lookup[name][0]

		for x in lookup[name]:
			if x["author"] == author:
				return x

	if link is not None and len(link) > 15:
		for x in list:
			if link in x["link"]:
				return x

	return None

def generateGitURL(urlstr):
	scheme, netloc, path, query, frag = urlsplit(urlstr)

	return "http://:@" + netloc + path + query


def getTempDir():
	return os.path.join(tempfile.gettempdir(), randomString(10))


# Clones a repo from an unvalidated URL.
# Returns a tuple of path and repo on sucess.
# Throws `TaskError` on failure.
# Caller is responsible for deleting returned directory.
def cloneRepo(urlstr, ref=None, recursive=False):
	gitDir = getTempDir()

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

		return gitDir, repo

	except GitCommandError as e:
		# This is needed to stop the backtrace being weird
		err = e.stderr

	except gitdb.exc.BadName as e:
		err = "Unable to find the reference " + (ref or "?") + "\n" + e.stderr

	raise TaskError(err.replace("stderr: ", "") \
			.replace("Cloning into '" + gitDir + "'...", "") \
			.strip())


@celery.task(bind=True)
def updateMetaFromRelease(self, id, path):
	release = PackageRelease.query.get(id)
	if release is None:
		raise TaskError("No such release!")
	elif release.package is None:
		raise TaskError("No package attached to release")

	temp = getTempDir()
	try:
		with ZipFile(path, 'r') as zip_ref:
			zip_ref.extractall(temp)

		try:
			tree = build_tree(temp, expected_type=ContentType[release.package.type.name], \
				author=release.package.author.username, name=release.package.name)

			cache = {}
			def getMetaPackages(names):
				return [ MetaPackage.GetOrCreate(x, cache) for x in names ]

			provides = getMetaPackages(tree.getModNames())

			package = release.package
			package.provides.clear()
			package.provides.extend(provides)

			for dep in package.dependencies:
				if dep.meta_package:
					db.session.delete(dep)

			for meta in getMetaPackages(tree.fold("meta", "depends")):
				db.session.add(Dependency(package, meta=meta, optional=False))

			for meta in getMetaPackages(tree.fold("meta", "optional_depends")):
				db.session.add(Dependency(package, meta=meta, optional=True))

			db.session.commit()

		except MinetestCheckError as err:
			if "Fails validation" not in release.title:
				release.title += " (Fails validation)"

			release.task_id = self.request.id
			release.approved = False
			db.session.commit()

			raise TaskError(str(err))

	finally:
		shutil.rmtree(temp)


@celery.task()
def getMeta(urlstr, author):
	gitDir, _ = cloneRepo(urlstr, recursive=True)

	try:
		tree = build_tree(gitDir, author=author, repo=urlstr)
	except MinetestCheckError as err:
		raise TaskError(str(err))

	shutil.rmtree(gitDir)

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


@celery.task(bind=True)
def checkZipRelease(self, id, path):
	release = PackageRelease.query.get(id)
	if release is None:
		raise TaskError("No such release!")
	elif release.package is None:
		raise TaskError("No package attached to release")

	temp = getTempDir()
	try:
		with ZipFile(path, 'r') as zip_ref:
			zip_ref.extractall(temp)

		try:
			tree = build_tree(temp, expected_type=ContentType[release.package.type.name], \
				author=release.package.author.username, name=release.package.name)
		except MinetestCheckError as err:
			if "Fails validation" not in release.title:
				release.title += " (Fails validation)"

			release.task_id = self.request.id
			release.approved = False
			db.session.commit()

			raise TaskError(str(err))

		release.task_id = None
		release.approve(release.package.author)
		db.session.commit()

	finally:
		shutil.rmtree(temp)


@celery.task()
def makeVCSRelease(id, branch):
	release = PackageRelease.query.get(id)
	if release is None:
		raise TaskError("No such release!")
	elif release.package is None:
		raise TaskError("No package attached to release")

	gitDir, repo = cloneRepo(release.package.repo, ref=branch, recursive=True)

	tree = None
	try:
		tree = build_tree(gitDir, expected_type=ContentType[release.package.type.name], \
			author=release.package.author.username, name=release.package.name)
	except MinetestCheckError as err:
		raise TaskError(str(err))

	try:
		filename = randomString(10) + ".zip"
		destPath = os.path.join(app.config["UPLOAD_DIR"], filename)

		assert(not os.path.isfile(destPath))
		archiver = GitArchiver(force_sub=True, main_repo_abspath=gitDir)
		archiver.create(destPath)
		assert(os.path.isfile(destPath))

		release.url         = "/uploads/" + filename
		release.task_id     = None
		release.commit_hash = repo.head.object.hexsha

		if tree.meta.get("min_minetest_version"):
			release.min_rel = MinetestRelease.get(tree.meta["min_minetest_version"], None)

		if tree.meta.get("max_minetest_version"):
			release.max_rel = MinetestRelease.get(tree.meta["max_minetest_version"], None)

		release.approve(release.package.author)
		db.session.commit()

		updateMetaFromRelease.delay(release.id, destPath)

		return release.url
	finally:
		shutil.rmtree(gitDir)


@celery.task()
def importRepoScreenshot(id):
	package = Package.query.get(id)
	if package is None or package.soft_deleted:
		raise Exception("Unexpected none package")

	# Get URL Maker
	try:
		gitDir, _ = cloneRepo(package.repo)
	except TaskError as e:
		# ignore download errors
		print(e)
		return None

	# Find and import screenshot
	try:
		for ext in ["png", "jpg", "jpeg"]:
			sourcePath = gitDir + "/screenshot." + ext
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
	finally:
		shutil.rmtree(gitDir)

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
		release.task_id = self.request.id
		release.approved = False
		db.session.commit()
