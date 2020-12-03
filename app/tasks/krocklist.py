# ContentDB
# Copyright (C) 2018-20 rubenwardy
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


import json
import urllib.request

krock_list_cache = None
krock_list_cache_by_name = None
def getKrockList():
	global krock_list_cache
	global krock_list_cache_by_name

	if krock_list_cache is None:
		contents = urllib.request.urlopen("https://krock-works.uk.to/minetest/modList.php").read().decode("utf-8")
		list = json.loads(contents)

		def h(x):
			if not ("title"   in x and "author" in x and \
					"topicId" in x and "link"   in x and x["link"] != ""):
				return False

			import re
			m = re.search(r"\[([A-Za-z0-9_]+)\]", x["title"])
			if m is None:
				return False

			x["name"] = m.group(1)
			return True

		def g(x):
			return {
				"title":   x["title"],
				"author":  x["author"],
				"name":	x["name"],
				"topicId": x["topicId"],
				"link":	x["link"],
			}

		krock_list_cache = [g(x) for x in list if h(x)]
		krock_list_cache_by_name = {}
		for x in krock_list_cache:
			if not x["name"] in krock_list_cache_by_name:
				krock_list_cache_by_name[x["name"]] = []

			krock_list_cache_by_name[x["name"]].append(x)

	return krock_list_cache, krock_list_cache_by_name


def findModInfo(author, name, link):
	list, lookup = getKrockList()

	if name is not None and name in lookup:
		if len(lookup[name]) == 1:
			return lookup[name][0]

		for x in lookup[name]:
			if x["author"] == author:
				return x

	if link is not None and len(link) > 15:
		for x in list:
			if link in x["link"]:
				return x

	return None
