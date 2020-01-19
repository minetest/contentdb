# Content DB
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
from app import app
from app.models import *
from app.tasks import celery, TaskError
from app.utils import randomString


class GithubURLMaker:
	def __init__(self, url):
		self.baseUrl = None
		self.user = None
		self.repo = None

		# Rewrite path
		import re
		m = re.search("^\/([^\/]+)\/([^\/]+)\/?$", url.path)
		if m is None:
			return

		user = m.group(1)
		repo = m.group(2).replace(".git", "")
		self.baseUrl = "https://raw.githubusercontent.com/{}/{}/master" \
				.format(user, repo)
		self.user = user
		self.repo = repo

	def isValid(self):
		return self.baseUrl is not None

	def getRepoURL(self):
		return "https://github.com/{}/{}".format(self.user, self.repo)

	def getScreenshotURL(self):
		return self.baseUrl + "/screenshot.png"

	def getModConfURL(self):
		return self.baseUrl + "/mod.conf"

	def getCommitsURL(self, branch):
		return "https://api.github.com/repos/{}/{}/commits?sha={}" \
				.format(self.user, self.repo, urllib.parse.quote_plus(branch))

	def getCommitDownload(self, commit):
		return "https://github.com/{}/{}/archive/{}.zip" \
				.format(self.user, self.repo, commit)

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


def parseConf(string):
	retval = {}
	for line in string.split("\n"):
		idx = line.find("=")
		if idx > 0:
			key   = line[:idx].strip()
			value = line[idx+1:].strip()
			retval[key] = value

	return retval


class PackageTreeNode:
	def __init__(self, baseDir, author=None, repo=None, name=None):
		print("Scanning " + baseDir)
		self.baseDir  = baseDir
		self.author   = author
		self.name	 = name
		self.repo	 = repo
		self.meta	 = None
		self.children = []

		# Detect type
		type = None
		is_modpack = False
		if os.path.isfile(baseDir + "/game.conf"):
			type = PackageType.GAME
		elif os.path.isfile(baseDir + "/init.lua"):
			type = PackageType.MOD
		elif os.path.isfile(baseDir + "/modpack.txt") or \
				os.path.isfile(baseDir + "/modpack.conf"):
			type = PackageType.MOD
			is_modpack = True
		elif os.path.isdir(baseDir + "/mods"):
			type = PackageType.GAME
		elif os.listdir(baseDir) == []:
			# probably a submodule
			return
		else:
			raise TaskError("Unable to detect package type!")

		self.type = type
		self.readMetaFiles()

		if self.type == PackageType.GAME:
			self.addChildrenFromModDir(baseDir + "/mods")
		elif is_modpack:
			self.addChildrenFromModDir(baseDir)


	def readMetaFiles(self):
		result = {}

		# .conf file
		try:
			with open(self.baseDir + "/mod.conf", "r") as myfile:
				conf = parseConf(myfile.read())
				for key in ["name", "description", "title", "depends", "optional_depends"]:
					try:
						result[key] = conf[key]
					except KeyError:
						pass
		except IOError:
			print("description.txt does not exist!")

		# description.txt
		if not "description" in result:
			try:
				with open(self.baseDir + "/description.txt", "r") as myfile:
					result["description"] = myfile.read()
			except IOError:
				print("description.txt does not exist!")

		# depends.txt
		import re
		pattern = re.compile("^([a-z0-9_]+)\??$")
		if not "depends" in result and not "optional_depends" in result:
			try:
				with open(self.baseDir + "/depends.txt", "r") as myfile:
					contents = myfile.read()
					soft = []
					hard = []
					for line in contents.split("\n"):
						line = line.strip()
						if pattern.match(line):
							if line[len(line) - 1] == "?":
								soft.append( line[:-1])
							else:
								hard.append(line)

					result["depends"] = hard
					result["optional_depends"] = soft

			except IOError:
				print("depends.txt does not exist!")

		else:
			if "depends" in result:
				result["depends"] = [x.strip() for x in result["depends"].split(",")]
			if "optional_depends" in result:
				result["optional_depends"] = [x.strip() for x in result["optional_depends"].split(",")]


		# Calculate Title
		if "name" in result and not "title" in result:
			result["title"] = result["name"].replace("_", " ").title()

		# Calculate short description
		if "description" in result:
			desc = result["description"]
			idx = desc.find(".") + 1
			cutIdx = min(len(desc), 200 if idx < 5 else idx)
			result["short_description"] = desc[:cutIdx]

		# Get forum ID
		info = findModInfo(self.author, result.get("name"), self.repo)
		if info is not None:
			result["forumId"] = info.get("topicId")

		if "name" in result:
			self.name = result["name"]
			del result["name"]

		self.meta = result

	def addChildrenFromModDir(self, dir):
		for entry in next(os.walk(dir))[1]:
			path = dir + "/" + entry
			if not entry.startswith('.') and os.path.isdir(path):
				self.children.append(PackageTreeNode(path, name=entry))


	def fold(self, attr, key=None, acc=None):
		if acc is None:
			acc = set()

		if self.meta is None:
			return acc

		at = getattr(self, attr)
		value = at if key is None else at.get(key)

		if isinstance(value, list):
			acc |= set(value)
		elif value is not None:
			acc.add(value)

		for child in self.children:
			child.fold(attr, key, acc)

		return acc

	def get(self, key):
		return self.meta.get(key)

def generateGitURL(urlstr):
	scheme, netloc, path, query, frag = urlsplit(urlstr)

	return "http://:@" + netloc + path + query

# Clones a repo from an unvalidated URL.
# Returns a tuple of path and repo on sucess.
# Throws `TaskError` on failure.
# Caller is responsible for deleting returned directory.
def cloneRepo(urlstr, ref=None, recursive=False):
	gitDir = tempfile.gettempdir() + "/" + randomString(10)

	err = None
	try:
		gitUrl = generateGitURL(urlstr)
		print("Cloning from " + gitUrl)

		if ref is None:
			repo = git.Repo.clone_from(gitUrl, gitDir, \
					progress=None, env=None, depth=1, recursive=recursive, kill_after_timeout=15)
		else:
			repo = git.Repo.clone_from(gitUrl, gitDir, \
					progress=None, env=None, depth=1, recursive=recursive, kill_after_timeout=15, b=ref)

		return gitDir, repo

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
	gitDir, _ = cloneRepo(urlstr, recursive=True)
	tree = PackageTreeNode(gitDir, author=author, repo=urlstr)
	shutil.rmtree(gitDir)

	result = {}
	result["name"] = tree.name
	result["provides"] = tree.fold("name")
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


def makeVCSReleaseFromGithub(id, branch, release, url):
	urlmaker = GithubURLMaker(url)
	if not urlmaker.isValid():
		raise TaskError("Invalid github repo URL")

	commitsURL = urlmaker.getCommitsURL(branch)
	try:
		contents = urllib.request.urlopen(commitsURL).read().decode("utf-8")
		commits = json.loads(contents)
	except HTTPError:
		raise TaskError("Unable to get commits for Github repository. Either the repository or reference doesn't exist.")

	if len(commits) == 0 or not "sha" in commits[0]:
		raise TaskError("No commits found")

	release.url          = urlmaker.getCommitDownload(commits[0]["sha"])
	release.task_id     = None
	release.commit_hash = commits[0]["sha"]
	release.approve(release.package.author)
	db.session.commit()

	return release.url



@celery.task()
def makeVCSRelease(id, branch):
	release = PackageRelease.query.get(id)
	if release is None:
		raise TaskError("No such release!")
	elif release.package is None:
		raise TaskError("No package attached to release")

	# url = urlparse(release.package.repo)
	# if url.netloc == "github.com":
	# 	return makeVCSReleaseFromGithub(id, branch, release, url)

	gitDir, repo = cloneRepo(release.package.repo, ref=branch, recursive=True)

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
		release.approve(release.package.author)
		print(release.url)
		db.session.commit()

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



def getDepends(package):
	url = urlparse(package.repo)
	urlmaker = None
	if url.netloc == "github.com":
		urlmaker = GithubURLMaker(url)
	else:
		return {}

	result = {}
	if not urlmaker.isValid():
		return {}

	#
	# Try getting depends on mod.conf
	#
	try:
		contents = urllib.request.urlopen(urlmaker.getModConfURL()).read().decode("utf-8")
		conf = parseConf(contents)
		for key in ["depends", "optional_depends"]:
			try:
				result[key] = conf[key]
			except KeyError:
				pass

	except HTTPError:
		print("mod.conf does not exist")

	if "depends" in result or "optional_depends" in result:
		return result


	#
	# Try depends.txt
	#
	import re
	pattern = re.compile("^([a-z0-9_]+)\??$")
	try:
		contents = urllib.request.urlopen(urlmaker.getDependsURL()).read().decode("utf-8")
		soft = []
		hard = []
		for line in contents.split("\n"):
			line = line.strip()
			if pattern.match(line):
				if line[len(line) - 1] == "?":
					soft.append( line[:-1])
				else:
					hard.append(line)

		result["depends"] = ",".join(hard)
		result["optional_depends"] = ",".join(soft)
	except HTTPError:
		print("depends.txt does not exist")

	return result


def importDependencies(package, mpackage_cache):
	if Dependency.query.filter_by(depender=package).count() != 0:
		return

	result = getDepends(package)

	if "depends" in result:
		deps = Dependency.SpecToList(package, result["depends"], mpackage_cache)
		print("{} hard: {}".format(len(deps), result["depends"]))
		for dep in deps:
			dep.optional = False
			db.session.add(dep)

	if "optional_depends" in result:
		deps = Dependency.SpecToList(package, result["optional_depends"], mpackage_cache)
		print("{} soft: {}".format(len(deps), result["optional_depends"]))
		for dep in deps:
			dep.optional = True
			db.session.add(dep)

@celery.task()
def importAllDependencies():
	Dependency.query.delete()
	mpackage_cache = {}
	packages = Package.query.filter_by(type=PackageType.MOD).all()
	for i, p in enumerate(packages):
		print("============= {} ({}/{}) =============".format(p.name, i, len(packages)))
		importDependencies(p, mpackage_cache)

	db.session.commit()
