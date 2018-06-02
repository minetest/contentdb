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


import flask, json
from flask.ext.sqlalchemy import SQLAlchemy
from app import app
from app.models import *
from app.tasks import celery
from .phpbbparser import getProfile
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

@celery.task()
def importUsersFromModList():
	contents = urllib.request.urlopen("http://krock-works.16mb.com/MTstuff/modList.php").read().decode("utf-8")
	list = json.loads(contents)
	found = {}
	imported = []

	for user in User.query.all():
		found[user.username] = True
		if user.forums_username is not None:
			found[user.forums_username] = True

	for x in list:
		author = x.get("author")
		if author is not None and not author in found:
			user = User(author)
			user.forums_username = author
			imported.append(author)
			found[author] = True
			db.session.add(user)

	db.session.commit()
	for author in found:
		checkForumAccount.delay(author, None)


BANNED_NAMES = ["mod", "game", "old", "outdated", "wip", "api"]
ALLOWED_TYPES = [1, 2, 6]

@celery.task()
def importKrocksModList():
	contents = urllib.request.urlopen("http://krock-works.16mb.com/MTstuff/modList.php").read().decode("utf-8")
	list = json.loads(contents)
	username_to_user = {}

	KrockForumTopic.query.delete()

	for x in list:
		type = int(x["type"])
		if not type in ALLOWED_TYPES:
			continue

		username = x["author"]
		user = username_to_user.get(username)
		if user is None:
			user = User.query.filter_by(forums_username=username).first()
			assert(user is not None)
			username_to_user[username] = user

		import re
		tags = re.findall("\[([a-z0-9_]+)\]", x["title"])
		name = None
		for tag in reversed(tags):
			if len(tag) < 50 and not tag in BANNED_NAMES and \
					not re.match("^([a-z][0-9]+)$", tag):
				name = tag
				break

		topic = KrockForumTopic()
		topic.topic_id  = x["topicId"]
		topic.author_id = user.id
		topic.ttype     = type
		topic.title     = x["title"]
		topic.name      = name
		topic.link      = x.get("link")
		db.session.add(topic)

	db.session.commit()
