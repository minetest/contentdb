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


import flask, json, os
from flask.ext.sqlalchemy import SQLAlchemy
from urllib.error import HTTPError
import urllib.request
from urllib.parse import urlparse, quote_plus
from app import app
from app.models import *
from app.tasks import celery, TaskError
from app.utils import randomString

class GithubURLMaker:
	def __init__(self, url):
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

	def getIssueTrackerURL(self):
		return "https://github.com/{}/{}/issues/".format(self.user, self.repo)

	def getModConfURL(self):
		return self.baseUrl + "/mod.conf"

	def getDescURL(self):
		return self.baseUrl + "/description.txt"

	def getScreenshotURL(self):
		return self.baseUrl + "/screenshot.png"

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
		contents = urllib.request.urlopen("http://krock-works.16mb.com/MTstuff/modList.php").read().decode("utf-8")
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
				"name":    x["name"],
				"topicId": x["topicId"],
				"link":    x["link"],
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


@celery.task()
def getMeta(urlstr, author):
	url = urlparse(urlstr)

	urlmaker = None
	if url.netloc == "github.com":
		urlmaker = GithubURLMaker(url)
	else:
		raise TaskError("Unsupported repo")

	if not urlmaker.isValid():
		raise TaskError("Error! Url maker not valid")

	result = {}

	result["repo"] = urlmaker.getRepoURL()
	result["issueTracker"] = urlmaker.getIssueTrackerURL()

	try:
		contents = urllib.request.urlopen(urlmaker.getModConfURL()).read().decode("utf-8")
		conf = parseConf(contents)
		for key in ["name", "description", "title"]:
			try:
				result[key] = conf[key]
			except KeyError:
				pass
	except HTTPError:
		print("mod.conf does not exist")

	if "name" in result:
		result["title"] = result["name"].replace("_", " ").title()

	if not "description" in result:
		try:
			contents = urllib.request.urlopen(urlmaker.getDescURL()).read().decode("utf-8")
			result["description"] = contents.strip()
		except HTTPError:
			print("description.txt does not exist!")

	if "description" in result:
		desc = result["description"]
		idx = desc.find(".") + 1
		cutIdx = min(len(desc), 200 if idx < 5 else idx)
		result["short_description"] = desc[:cutIdx]

	info = findModInfo(author, result.get("name"), result["repo"])
	if info is not None:
		result["forumId"] = info.get("topicId")

	return result


@celery.task()
def makeVCSRelease(id, branch):
	release = PackageRelease.query.get(id)

	if release is None:
		raise TaskError("No such release!")

	if release.package is None:
		raise TaskError("No package attached to release")

	url = urlparse(release.package.repo)

	urlmaker = None
	if url.netloc == "github.com":
		urlmaker = GithubURLMaker(url)
	else:
		raise TaskError("Unsupported repo")

	if not urlmaker.isValid():
		raise TaskError("Invalid github repo URL")

	commitsURL = urlmaker.getCommitsURL(branch)
	contents = urllib.request.urlopen(commitsURL).read().decode("utf-8")
	commits = json.loads(contents)

	if len(commits) == 0 or not "sha" in commits[0]:
		raise TaskError("No commits found")

	release.url = urlmaker.getCommitDownload(commits[0]["sha"])
	print(release.url)
	release.task_id = None
	db.session.commit()

	return release.url


@celery.task()
def importRepoScreenshot(id):
	package = Package.query.get(id)
	if package is None:
		raise Exception("Unexpected none package")

	# Get URL Maker
	url = urlparse(package.repo)
	urlmaker = None
	if url.netloc == "github.com":
		urlmaker = GithubURLMaker(url)
	else:
		raise TaskError("Unsupported repo")

	if not urlmaker.isValid():
		raise TaskError("Error! Url maker not valid")

	try:
		filename = randomString(10) + ".png"
		imagePath = os.path.join("public/uploads", filename)
		print(imagePath)
		urllib.request.urlretrieve(urlmaker.getScreenshotURL(), imagePath)

		ss = PackageScreenshot()
		ss.package = package
		ss.title   = "screenshot.png"
		ss.url     = "/uploads/" + filename
		db.session.add(ss)
		db.session.commit()

		return "/uploads/" + filename
	except HTTPError:
		print("screenshot.png does not exist")

	return None
