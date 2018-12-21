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


import flask, json, re
from flask.ext.sqlalchemy import SQLAlchemy
from app import app
from app.models import *
from app.tasks import celery
from .phpbbparser import getProfile, getTopicsFromForum
import urllib.request
from urllib.parse import urlparse, quote_plus

@celery.task()
def checkForumAccount(username, token=None):
	try:
		profile = getProfile("https://forum.minetest.net", username)
	except OSError:
		return

	user = User.query.filter_by(forums_username=username).first()

	# Create user
	needsSaving = False
	if user is None:
		user = User(username)
		user.forums_username = username
		db.session.add(user)

	# Get github username
	github_username = profile.get("github")
	if github_username is not None and github_username.strip() != "":
		print("Updated github username for " + user.display_name + " to " + github_username)
		user.github_username = github_username
		needsSaving = True

	# Save
	if needsSaving:
		db.session.commit()


regex_tag    = re.compile(r"\[([a-z0-9_]+)\]")
BANNED_NAMES = ["mod", "game", "old", "outdated", "wip", "api", "beta", "alpha", "git"]
def getNameFromTaglist(taglist):
	for tag in reversed(regex_tag.findall(taglist)):
		if len(tag) < 30 and not tag in BANNED_NAMES and \
				not re.match(r"^[a-z]?[0-9]+$", tag):
			return tag

	return None

regex_title = re.compile(r"^((?:\[[^\]]+\] *)*)([^\[]+) *((?:\[[^\]]+\] *)*)[^\[]*$")
def parseTitle(title):
	m = regex_title.match(title)
	if m is None:
		print("Invalid title format: " + title)
		return title, getNameFromTaglist(title)
	else:
		return m.group(2).strip(), getNameFromTaglist(m.group(3))

def getLinksFromModSearch():
	links = {}

	contents = urllib.request.urlopen("https://krock-works.uk.to/minetest/modList.php").read().decode("utf-8")
	for x in json.loads(contents):
		link = x.get("link")
		if link is not None:
			links[int(x["topicId"])] = link

	return links

@celery.task()
def importTopicList():
	links_by_id = getLinksFromModSearch()

	info_by_id = {}
	getTopicsFromForum(11, out=info_by_id, extra={ 'type': PackageType.MOD,  'wip': False })
	getTopicsFromForum(9,  out=info_by_id, extra={ 'type': PackageType.MOD,  'wip': True  })
	getTopicsFromForum(15, out=info_by_id, extra={ 'type': PackageType.GAME, 'wip': False })
	getTopicsFromForum(50, out=info_by_id, extra={ 'type': PackageType.GAME, 'wip': True  })

	# Caches
	username_to_user = {}
	topics_by_id     = {}
	for topic in ForumTopic.query.all():
		topics_by_id[topic.topic_id] = topic

	# Create or update
	for info in info_by_id.values():
		id = int(info["id"])

		# Get author
		username = info["author"]
		user = username_to_user.get(username)
		if user is None:
			user = User.query.filter_by(forums_username=username).first()
			if user is None:
				print(username + " not found!")
				user = User(username)
				user.forums_username = username
				db.session.add(user)
			username_to_user[username] = user

		# Get / add row
		topic = topics_by_id.get(id)
		if topic is None:
			topic = ForumTopic()
			db.session.add(topic)

		# Parse title
		title, name = parseTitle(info["title"])

		# Get link
		link = links_by_id.get(id)

		# Fill row
		topic.topic_id   = int(id)
		topic.author     = user
		topic.type       = info["type"]
		topic.title      = title
		topic.name       = name
		topic.link       = link
		topic.wip        = info["wip"]
		topic.posts      = int(info["posts"])
		topic.views      = int(info["views"])
		topic.created_at = info["date"]

	for p in Package.query.all():
		p.recalcScore()

	db.session.commit()
