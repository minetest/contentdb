import flask
from flask.ext.sqlalchemy import SQLAlchemy
from app import app
from app.models import *
from app.tasks import celery
from .phpbbparser import getProfile

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
		print("Updated github username")
		user.github_username = github_username
		needsSaving = True

	# Save
	if needsSaving:
		db.session.commit()
