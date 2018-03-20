import os, sys, datetime

delete_db = len(sys.argv) >= 2 and sys.argv[1].strip() == "-d"

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

	mod1 = Package()
	mod1.name = "awards"
	mod1.title = "Awards"
	mod1.type = PackageType.MOD
	mod1.author = ruben
	mod1.shortDesc = "Adds achievements and an API to register new ones."
	mod1.desc = """
	Majority of awards are back ported from Calinou's old fork in Carbone, under same license.

```
awards.register_achievement("award_mesefind",{
    title = "First Mese Find",
    description = "Found some Mese!",
    trigger = {
        type   = "dig",          -- award is given when
        node   = "default:mese", -- this type of node has been dug
        target = 1,              -- this number of times
    },
})
```
	"""
	mod1.repo = "https://github.com/rubenwardy/awards"
	mod1.issueTracker = "https://github.com/rubenwardy/awards/issues"
	mod1.forums = "https://forum.minetest.net/viewtopic.php?t=4870"
	db.session.add(mod1)

	db.session.commit()
else:
	print("Database already exists")
