# ContentDB
# Copyright (C) rubenwardy
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

from . import r

# This file acts as a facade between the releases code and redis,
# and also means that the releases code avoids knowing about `app`

def make_download_key(ip, package):
	return "{}/{}/{}".format(ip, package.author.username, package.name)

def set_key(key, v):
	r.set(key, v)

def has_key(key):
	return r.exists(key)
