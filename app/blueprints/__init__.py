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

import importlib
import os


def create_blueprints(app):
	dir = os.path.dirname(os.path.realpath(__file__))
	modules = next(os.walk(dir))[1]	
	
	for modname in modules:		
		if all(c.islower() for c in modname):
			module = importlib.import_module("." + modname, __name__)		
			app.register_blueprint(module.bp)
