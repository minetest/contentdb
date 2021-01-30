# ContentDB
# Copyright (C) 2018-21 rubenwardy
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


import json, re, sys
from app.models import *
from app.tasks import celery
from .phpbbparser import getProfile, getTopicsFromForum
import urllib.request

@celery.task()
def checkForumAccount(username, forceNoSave=False):
	print("Checking " + username)
	try:
		profile = getProfile("https://forum.minetest.net", username)
	except OSError:
		return

	if profile is None:
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

	pic = profile.avatar
	if pic and "http" in pic:
		pic = None

	needsSaving = needsSaving or pic != user.profile_pic
	if pic:
		user.profile_pic = "https://forum.minetest.net/" + pic
	else:
		user.profile_pic = None

	# Save
	if needsSaving and not forceNoSave:
		db.session.commit()

	return needsSaving


@celery.task()
def checkAllForumAccounts(forceNoSave=False):
	needsSaving = False
	query = User.query.filter(User.forums_username.isnot(None))
	for user in query.all():
		needsSaving = checkForumAccount(user.username) or needsSaving

	if needsSaving and not forceNoSave:
		db.session.commit()

	return needsSaving


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

	try:
		contents = urllib.request.urlopen("https://krock-works.uk.to/minetest/modList.php").read().decode("utf-8")
		for x in json.loads(contents):
			try:
				link = x.get("link")
				if link is not None:
					links[int(x["topicId"])] = link
			except ValueError:
				pass

	except urllib.error.URLError:
		print("Unable to open krocks mod search!")
		return links

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

	def get_or_create_user(username):
		user = username_to_user.get(username)
		if user:
			return user

		user = User.query.filter_by(forums_username=username).first()
		if user is None:
			user = User.query.filter_by(username=username).first()
			if user:
				return None

			user = User(username)
			user.forums_username = username
			db.session.add(user)

		username_to_user[username] = user
		return user

	# Create or update
	for info in info_by_id.values():
		id = int(info["id"])

		# Get author
		username = info["author"]
		user = get_or_create_user(username)
		if user is None:
			print("Error! Unable to create user {}".format(username), file=sys.stderr)
			continue

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

	db.session.commit()
