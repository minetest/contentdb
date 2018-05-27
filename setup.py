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


import os, sys, datetime

if not "FLASK_CONFIG" in os.environ:
	os.environ["FLASK_CONFIG"] = "../config.cfg"

test_data = len(sys.argv) >= 2 and sys.argv[1].strip() == "-t"

from app.models import *

def defineDummyData(licenses, tags, ruben):
	ez = User("Shara")
	ez.github_username = "Ezhh"
	ez.forums_username = "Shara"
	ez.rank = UserRank.EDITOR
	db.session.add(ez)

	not1 = Notification(ruben, ez, "Awards approved", "/packages/rubenwardy/awards/")
	db.session.add(not1)

	jeija = User("Jeija")
	jeija.github_username = "Jeija"
	db.session.add(jeija)


	mod = Package()
	mod.approved = True
	mod.name = "alpha"
	mod.title = "Alpha Test"
	mod.license = licenses["MIT"]
	mod.type = PackageType.MOD
	mod.author = ruben
	mod.tags.append(tags["mapgen"])
	mod.tags.append(tags["environment"])
	mod.repo = "https://github.com/ezhh/other_worlds"
	mod.issueTracker = "https://github.com/ezhh/other_worlds/issues"
	mod.forums = 16015
	mod.shortDesc = "The content library should not be used yet as it is still in alpha"
	mod.desc = "This is the long desc"
	db.session.add(mod)

	rel = PackageRelease()
	rel.package = mod
	rel.title = "v1.0.0"
	rel.url = "https://github.com/ezhh/handholds/archive/master.zip"
	rel.approved = True
	db.session.add(rel)

	mod1 = Package()
	mod1.approved = True
	mod1.name = "awards"
	mod1.title = "Awards"
	mod1.license = licenses["LGPLv2.1"]
	mod1.type = PackageType.MOD
	mod1.author = ruben
	mod1.tags.append(tags["player_effects"])
	mod1.repo = "https://github.com/rubenwardy/awards"
	mod1.issueTracker = "https://github.com/rubenwardy/awards/issues"
	mod1.forums = 4870
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

	rel = PackageRelease()
	rel.package = mod1
	rel.title = "v1.0.0"
	rel.url = "https://github.com/rubenwardy/awards/archive/master.zip"
	rel.approved = True
	db.session.add(rel)

	mod2 = Package()
	mod2.approved = True
	mod2.name = "mesecons"
	mod2.title = "Mesecons"
	mod2.tags.append(tags["tools"])
	mod2.type = PackageType.MOD
	mod2.license = licenses["LGPLv3"]
	mod2.author = jeija
	mod2.repo = "https://github.com/minetest-mods/mesecons/"
	mod2.issueTracker = "https://github.com/minetest-mods/mesecons/issues"
	mod2.forums = 628
	mod2.shortDesc = "Mesecons adds everything digital, from all kinds of sensors, switches, solar panels, detectors, pistons, lamps, sound blocks to advanced digital circuitry like logic gates and programmable blocks."
	mod2.desc = """
    ########################################################################
    ##  __    __   _____   _____   _____   _____   _____   _   _   _____  ##
    ## |  \  /  | |  ___| |  ___| |  ___| |  ___| |  _  | | \ | | |  ___| ##
    ## |   \/   | | |___  | |___  | |___  | |     | | | | |  \| | | |___  ##
    ## | |\__/| | |  ___| |___  | |  ___| | |     | | | | |     | |___  | ##
    ## | |    | | | |___   ___| | | |___  | |___  | |_| | | |\  |  ___| | ##
    ## |_|    |_| |_____| |_____| |_____| |_____| |_____| |_| \_| |_____| ##
    ##                                                                    ##
    ########################################################################

MESECONS by Jeija and contributors

Mezzee-what?
------------
[Mesecons](http://mesecons.net/)! They're yellow, they're conductive, and they'll add a whole new dimension to Minetest's gameplay.

Mesecons is a mod for [Minetest](http://minetest.net/) that implements a ton of items related to digital circuitry, such as wires, buttons, lights, and even programmable controllers. Among other things, there are also pistons, solar panels, pressure plates, and note blocks.

Mesecons has a similar goal to Redstone in Minecraft, but works in its own way, with different rules and mechanics.

OK, I want in.
--------------
Go get it!

[DOWNLOAD IT NOW](https://github.com/minetest-mods/mesecons/archive/master.zip)

Now go ahead and install it like any other Minetest mod. Don't know how? Check out [the wonderful page about it](http://wiki.minetest.com/wiki/Mods) over at the Minetest Wiki. For your convenience, here's a quick summary:

1. If Mesecons is still in a ZIP file, extract the folder inside to somewhere on the computer.
2. Make sure that when you open the folder, you can directly find `README.md` in the listing. If you just see another folder, move that folder up one level and delete the old one.
3. Open up the Minetest mods folder - usually `/mods/`. If you see the `minetest` or folder inside of that, that is your mod folder instead.
4. Copy the Mesecons folder into the mods folder.

Don't like some parts of Mesecons? Open up the Mesecons folder and delete the subfolder containing the mod you don't want. If you didn't want movestones, for example, all you have to do is delete the `mesecons_movestones` folder and they will no longer be available.

There are no dependencies - it will work right after installing!

How do I use this thing?
------------------------
How about a [quick overview video](https://www.youtube.com/watch?v=6kmeQj6iW5k)?

Or maybe a [comprehensive reference](http://mesecons.net/items.html) is your style?

An overview for the very newest of new beginners? How does [this one](http://uberi.mesecons.net/projects/MeseconsBasics/index.html) look?

Want to get more into building? Why not check out the [Mesecons Laboratory](http://uberi.mesecons.net/), a website dedicated to advanced Mesecons builders?

Want to contribute to Mesecons itself? Check out the [source code](https://github.com/minetest-mods/mesecons)!

Who wrote it anyways?
---------------------
These awesome people made Mesecons possible!

| Contributor     | Contribution                     |
| --------------- | -------------------------------- |
| Hawk777         | Code for VoxelManip caching      |
| Jat15           | Various tweaks.                  |
| Jeija           | **Main developer! Everything.**  |
| Jordach         | Noteblock sounds.                |
| khonkhortistan  | Code, recipes, textures.         |
| Kotolegokot     | Nodeboxes for items.             |
| minerd247       | Textures.                        |
| Nore/Novatux    | Code.                            |
| RealBadAngel    | Fixes, improvements.             |
| sfan5           | Code, recipes, textures.         |
| suzenako        | Piston sounds.                   |
| Uberi/Temperest | Code, textures, documentation.   |
| VanessaE        | Code, recipes, textures, design. |
| Whiskers75      | Logic gates implementation.      |

There are also a whole bunch of other people helping with everything from code to testing and feedback. Mesecons would also not be possible without their help!

Alright, how can I use it?
--------------------------
All textures in this project are licensed under the CC-BY-SA 3.0 (Creative Commons Attribution-ShareAlike 3.0 Generic). That means you can distribute and remix them as much as you want to, under the condition that you give credit to the authors and the project, and that if you remix and release them, they must be under the same or similar license to this one.

All code in this project is licensed under the LGPL version 3 or later. That means you have unlimited freedom to distribute and modify the work however you see fit, provided that if you decide to distribute it or any modified versions of it, you must also use the same license. The LGPL also grants the additional freedom to write extensions for the software and distribute them without the extensions being subject to the terms of the LGPL, although the software itself retains its license.

No warranty is provided, express or implied, for any part of the project.

"""

	db.session.add(mod1)
	db.session.add(mod2)

	mod = Package()
	mod.approved = True
	mod.name = "handholds"
	mod.title = "Handholds"
	mod.license = licenses["MIT"]
	mod.type = PackageType.MOD
	mod.author = ez
	mod.tags.append(tags["player_effects"])
	mod.repo = "https://github.com/ezhh/handholds"
	mod.issueTracker = "https://github.com/ezhh/handholds/issues"
	mod.forums = 17069
	mod.shortDesc = "Adds hand holds and climbing thingies"
	mod.desc = "This is the long desc"
	db.session.add(mod)

	rel = PackageRelease()
	rel.package = mod
	rel.title = "v1.0.0"
	rel.url = "https://github.com/ezhh/handholds/archive/master.zip"
	rel.approved = True
	db.session.add(rel)

	mod = Package()
	mod.approved = True
	mod.name = "other_worlds"
	mod.title = "Other Worlds"
	mod.license = licenses["MIT"]
	mod.type = PackageType.MOD
	mod.author = ez
	mod.tags.append(tags["mapgen"])
	mod.tags.append(tags["environment"])
	mod.repo = "https://github.com/ezhh/other_worlds"
	mod.issueTracker = "https://github.com/ezhh/other_worlds/issues"
	mod.forums = 16015
	mod.shortDesc = "Adds space with asteroids and comets"
	mod.desc = "This is the long desc"
	db.session.add(mod)

	mod = Package()
	mod.approved = True
	mod.name = "food"
	mod.title = "Food"
	mod.license = licenses["LGPLv2.1"]
	mod.type = PackageType.MOD
	mod.author = ruben
	mod.tags.append(tags["player_effects"])
	mod.repo = "https://github.com/rubenwardy/food/"
	mod.issueTracker = "https://github.com/rubenwardy/food/issues/"
	mod.forums = 2960
	mod.shortDesc = "Adds lots of food and an API to manage ingredients"
	mod.desc = "This is the long desc"
	food = mod
	db.session.add(mod)

	mod = Package()
	mod.approved = True
	mod.name = "food_sweet"
	mod.title = "Sweet Foods"
	mod.license = licenses["CC0"]
	mod.type = PackageType.MOD
	mod.author = ruben
	mod.tags.append(tags["player_effects"])
	mod.repo = "https://github.com/rubenwardy/food_sweet/"
	mod.issueTracker = "https://github.com/rubenwardy/food_sweet/issues/"
	mod.forums = 9039
	mod.shortDesc = "Adds sweet food"
	mod.desc = "This is the long desc"
	food_sweet = mod
	db.session.add(mod)

	game1 = Package()
	game1.approved = True
	game1.name = "capturetheflag"
	game1.title = "Capture The Flag"
	game1.type = PackageType.GAME
	game1.license = licenses["LGPLv2.1"]
	game1.author = ruben
	game1.tags.append(tags["pvp"])
	game1.tags.append(tags["survival"])
	game1.tags.append(tags["multiplayer"])
	game1.repo = "https://github.com/rubenwardy/capturetheflag"
	game1.issueTracker = "https://github.com/rubenwardy/capturetheflag/issues"
	game1.forums = 12835
	game1.shortDesc = "Two teams battle to snatch and return the enemy's flag, before the enemy takes their own!"
	game1.desc = """
As seen on the Capture the Flag server (minetest.rubenwardy.com:30000)

Uses the CTF PvP Engine.
"""

	db.session.add(game1)

	rel = PackageRelease()
	rel.package = game1
	rel.title = "v1.0.0"
	rel.url = "https://github.com/rubenwardy/capturetheflag/archive/master.zip"
	rel.approved = True
	db.session.add(rel)


	mod = Package()
	mod.approved = True
	mod.name = "pixelbox"
	mod.title = "PixelBOX Reloaded"
	mod.license = licenses["CC0"]
	mod.type = PackageType.TXP
	mod.author = ruben
	mod.forums = 14132
	mod.shortDesc = "This is an update of the original PixelBOX texture pack by the brillant artist Gambit"
	mod.desc = "This is the long desc"
	db.session.add(mod)

	rel = PackageRelease()
	rel.package = mod
	rel.title = "v1.0.0"
	rel.url = "http://mamadou3.free.fr/Minetest/PixelBOX.zip"
	rel.approved = True
	db.session.add(rel)

	db.session.commit()

	metas = {}
	for package in Package.query.filter_by(type=PackageType.MOD).all():
		meta = None
		try:
			meta = metas[package.name]
		except KeyError:
			meta = MetaPackage(package.name)
			db.session.add(meta)
			metas[package.name] = meta
		package.provides.append(meta)

	dep = Dependency(food_sweet, meta=metas["food"])
	db.session.add(dep)



delete_db = len(sys.argv) >= 2 and sys.argv[1].strip() == "-d"
if delete_db and os.path.isfile("db.sqlite"):
	os.remove("db.sqlite")

print("Creating database tables...")
db.create_all()
print("Filling database...")

ruben = User("rubenwardy")
ruben.github_username = "rubenwardy"
ruben.forums_username = "rubenwardy"
ruben.rank = UserRank.ADMIN
db.session.add(ruben)

tags = {}
for tag in ["Inventory", "Mapgen", "Building", \
		"Mobs and NPCs", "Tools", "Player effects", \
		"Environment", "Transport", "Maintenance", "Plants and farming", \
		"PvP", "PvE", "Survival", "Creative", "Puzzle", "Multiplayer", "Singleplayer"]:
	row = Tag(tag)
	tags[row.name] = row
	db.session.add(row)

licenses = {}
for license in ["GPLv2.1", "GPLv3", "LGPLv2.1", "LGPLv3", "AGPLv2.1", "AGPLv3",
				"Apache", "BSD 3-Clause", "BSD 2-Clause", "CC0", "CC-BY-SA",
				"CC-BY", "CC-BY-NC-SA", "MIT", "ZLib"]:
	row = License(license)
	licenses[row.name] = row
	db.session.add(row)

if test_data:
	defineDummyData(licenses, tags, ruben)

db.session.commit()
