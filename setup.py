import os, datetime

delete_db = False

if delete_db and os.path.isfile("app/data.sqlite"):
	os.remove("app/data.sqlite")

if not os.path.isfile("app/data.sqlite"):
	from app.models import *

	print("Creating database tables...")
	db.create_all()
	print("Filling database...")

	ruben = User("rubenwardy")
	ruben.github_username = "rubenwardy"
	db.session.add(ruben)
	db.session.commit()
else:
	print("Database already exists")
