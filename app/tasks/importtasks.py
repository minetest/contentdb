import flask, json
from flask.ext.sqlalchemy import SQLAlchemy
import urllib.request
from urllib.parse import urlparse, quote_plus
from app import app
from app.models import *
from app.tasks import celery

class TaskError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)


class GithubURLMaker:
	def __init__(self, url):
		# Rewrite path
		import re
		m = re.search("^\/([^\/]+)\/([^\/]+)\/?$", url.path)
		if m is None:
			return

		user = m.group(1)
		repo = m.group(2)
		self.baseUrl = "https://raw.githubusercontent.com/" + user + "/" + repo.replace(".git", "") + "/master"
		self.user = user
		self.repo = repo

	def isValid(self):
		return self.baseUrl is not None

	def getRepoURL(self):
		return "https://github.com/" + self.user + "/" + self.repo + ".git"

	def getIssueTrackerURL(self):
		return "https://github.com/" + self.user + "/" + self.repo + "/issues/"

	def getModConfURL(self):
		return self.baseUrl + "/mod.conf"

	def getDescURL(self):
		return self.baseUrl + "/description.txt"

	def getScreenshotURL(self):
		return self.baseUrl + "/screenshot.png"

	def getCommitsURL(self, branch):
		return "https://api.github.com/repos/" + self.user + "/" + self.repo + "/commits?sha" + urllib.parse.quote_plus(branch)

	def getCommitDownload(self, commit):
		return "https://github.com/" + self.user + "/" + self.repo + "/archive/" + commit + ".zip"


def parseConf(string):
	retval = {}
	for line in string.split("\n"):
		idx = line.find("=")
		if idx > 0:
			key   = line[:idx-1].strip()
			value = line[idx+1:].strip()
			retval[key] = value

	return retval

@celery.task()
def getMeta(urlstr):
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
	except OSError:
		print("mod.conf does not exist")

	if "name" in result:
		result["title"] = result["name"].replace("_", " ").title()

	if not "description" in result:
		try:
			contents = urllib.request.urlopen(urlmaker.getDescURL()).read().decode("utf-8")
			result["description"] = contents.strip()
		except OSError:
			print("description.txt does not exist!")

	if "description" in result:
		desc = result["description"]
		idx = desc.find(".") + 1
		cutIdx = min(len(desc), 200 if idx < 5 else idx)
		result["short_description"] = desc[:cutIdx]

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

	contents = urllib.request.urlopen(urlmaker.getCommitsURL(branch)).read().decode("utf-8")
	commits = json.loads(contents)

	if len(commits) == 0:
		raise TaskError("No commits found")

	release.url = urlmaker.getCommitDownload(commits[0]["sha"])
	release.task_id = None
	db.session.commit()

	return release.url
