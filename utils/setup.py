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


import inspect
import os
import sys



if not "FLASK_CONFIG" in os.environ:
	os.environ["FLASK_CONFIG"] = "../config.cfg"

delete_db = len(sys.argv) >= 2 and sys.argv[1].strip() == "-d"
create_db = not (len(sys.argv) >= 2 and sys.argv[1].strip() == "-o")
test_data = len(sys.argv) >= 2 and sys.argv[1].strip() == "-t" or not create_db

# Allow finding the `app` module
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from app.models import db
from app.default_data import populate, populate_test_data

if delete_db and os.path.isfile("db.sqlite"):
	os.remove("db.sqlite")

from app import app
with app.app_context():
	if create_db:
		print("Creating database tables...")
		db.create_all()

	print("Filling database...")

	populate(db.session)
	if test_data:
		populate_test_data(db.session)

	db.session.commit()
