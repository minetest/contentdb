import os, datetime

delete_db = False

if delete_db and os.path.isfile("app/data.sqlite"):
	os.remove("app/data.sqlite")

if not os.path.isfile("app/data.sqlite"):
	from app import models

	print("Creating database tables...")
	models.db.create_all()

	print("Filling database...")
	models.db.session.commit()
else:
	print("Database already exists")
