# Copyright (c) 2016  Andrew "rubenwardy" Ward
# License: MIT
# Source: https://github.com/rubenwardy/python_phpbb_parser

import re
import urllib
import urllib.parse as urlparse
import urllib.request
from datetime import datetime
from urllib.parse import urlencode
from bs4 import *


def urlEncodeNonAscii(b):
	return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

class Profile:
	def __init__(self, username):
		self.username   = username
		self.signature  = ""
		self.avatar     = None
		self.properties = {}

	def set(self, key, value):
		self.properties[key.lower()] = value

	def get(self, key):
		return self.properties.get(key.lower())

	def __str__(self):
		return self.username + "\n" + str(self.signature) + "\n" + str(self.properties)

def __extract_properties(profile, soup):
	el = soup.find(id="viewprofile")
	if el is None:
		return None

	res1 = el.find_all("dl")
	imgs = res1[0].find_all("img")
	if len(imgs) == 1:
		profile.avatar = imgs[0]["src"]

	res = el.select("dl.left-box.details")
	if len(res) != 1:
		return None

	catch_next_key = None

	# Look through
	for element in res[0].children:
		if element.name == "dt":
			if catch_next_key is None:
				catch_next_key = element.text.lower()[:-1].strip()
			else:
				print("Unexpected dt!")

		elif element.name == "dd":
			if catch_next_key is None:
				print("Unexpected dd!")
			else:
				if catch_next_key != "groups":
					profile.set(catch_next_key, element.text)
				catch_next_key = None

		elif element and element.name is not None:
			print("Unexpected other")

def __extract_signature(soup):
	res = soup.find_all("div", class_="signature")
	if len(res) != 1:
		return None
	else:
		return res[0]


def getProfileURL(url, username):
	url = urlparse.urlparse(url)

	# Update path
	url = url._replace(path="/memberlist.php")

	# Set query args
	query = dict(urlparse.parse_qsl(url.query))
	query.update({ "un": username, "mode": "viewprofile" })
	query_encoded = urlencode(query)
	url = url._replace(query=query_encoded)

	return urlparse.urlunparse(url)


def getProfile(url, username):
	url = getProfileURL(url, username)

	req = urllib.request.urlopen(url, timeout=5)
	if req.getcode() == 404:
		return None

	if req.getcode() != 200:
		raise IOError(req.getcode())

	contents = req.read().decode("utf-8")
	soup = BeautifulSoup(contents, "lxml")
	if soup is None:
		return None

	profile = Profile(username)
	profile.signature = __extract_signature(soup)
	__extract_properties(profile, soup)

	return profile


regex_id = re.compile(r"^.*t=([0-9]+).*$")

def parseForumListPage(id, page, out, extra=None):
	num_per_page = 30
	start = page*num_per_page+1
	print(" - Fetching page {} (topics {}-{})".format(page, start, start+num_per_page))

	url = "https://forum.minetest.net/viewforum.php?f=" + str(id) + "&start=" + str(start)
	r = urllib.request.urlopen(url).read().decode("utf-8")
	soup = BeautifulSoup(r, "html.parser")

	for row in soup.find_all("li", class_="row"):
		classes = row.get("class")
		if "sticky" in classes or "announce" in classes or "global-announce" in classes:
			continue

		topic = row.find("dl")

		# Link info
		link   = topic.find(class_="topictitle")
		id	   = regex_id.match(link.get("href")).group(1)
		title  = link.find(text=True)

		# Date
		left   = topic.find(class_="topic-poster")
		date   = left.find("time").get_text()
		date   = datetime.strptime(date, "%a %b %d, %Y %H:%M")
		author = left.find_all("a")[-1].get_text().strip()

		# Get counts
		posts  = topic.find(class_="posts").find(text=True)
		views  = topic.find(class_="views").find(text=True)

		if id in out:
			print("   - got {} again, title: {}".format(id, title))
			assert title == out[id]['title']
			return False

		row = {
			"id"    : id,
			"title" : title,
			"author": author,
			"posts" : posts,
			"views" : views,
			"date"  : date
		}

		if extra is not None:
			for key, value in extra.items():
				row[key] = value

		out[id] = row

	return True

def getTopicsFromForum(id, out, extra=None):
	print("Fetching all topics from forum {}".format(id))
	page = 0
	while parseForumListPage(id, page, out, extra):
		page = page + 1

	return out

def dumpTitlesToFile(topics, path):
	with open(path, "w") as out_file:
		for topic in topics.values():
			out_file.write(topic["title"] + "\n")
