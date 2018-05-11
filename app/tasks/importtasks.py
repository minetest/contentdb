import flask
from flask.ext.sqlalchemy import SQLAlchemy
import urllib.request
from urllib.parse import urlparse

from app import app
from app.models import *
from app.tasks import celery

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

	def isValid(self):
		return self.baseUrl is not None

	def getModConfURL(self):
		return self.baseUrl + "/mod.conf"

	def getDescURL(self):
		return self.baseUrl + "/description.txt"

	def getScreenshotURL(self):
		return self.baseUrl + "/screenshot.png"

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

	if not urlmaker.isValid():
		print("Error! Url maker not valid")
		return

	print(urlmaker.getModConfURL())

	result = {}

	try:
		contents = urllib.request.urlopen(urlmaker.getModConfURL()).read().decode("utf-8")
		conf = parseConf(contents)
		for key in ["name", "description", "title"]:
			try:
				result[key] = conf[key]
			except KeyError:
				pass

		print(conf)
	except OSError:
		print("mod.conf does not exist")

	if not "description" in result:
		try:
			contents = urllib.request.urlopen(urlmaker.getDescURL()).read().decode("utf-8")
			result["description"] = contents.strip()
		except OSError:
			print("description.txt does not exist!")

	return result
