import os, datetime

delete_db = False

if delete_db and os.path.isfile("db.sqlite"):
	os.remove("db.sqlite")

if not os.path.isfile("db.sqlite"):
	from app.models import *

	print("Creating database tables...")
	db.create_all()
	print("Filling database...")

	ruben = User("rubenwardy")
	ruben.github_username = "rubenwardy"
	db.session.add(ruben)

	mod1 = Mod()
	mod1.name = "awards"
	mod1.title = "Awards"
	mod1.author = ruben
	mod1.description = "Adds achievements and an API to register new ones."
	mod1.repo = "https://github.com/rubenwardy/awards"
	mod1.issueTracker = "https://github.com/rubenwardy/awards/issues"
	mod1.forums = "https://forum.minetest.net/viewtopic.php?t=4870"
	db.session.add(mod1)

	db.session.commit()
else:
	print("Database already exists")
