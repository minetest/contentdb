import json
import requests


__author__ = "AFCM <afcm.contact@gmail.com>"

SERVER = "http://content.minetest.net"

# FETCH LICENSES

print("Fetching Licenses")

res_licenses = requests.get(SERVER + "/api/licenses/").json()

licenses_names = []
licenses_descs = []

for i in res_licenses:
    licenses_names.append(i["name"])
    licenses_descs.append(i["is_foss"] and "FOSS" or "NON-FOSS")


# FETCH TAGS

print("Fetching Tags")

res_tags = requests.get(SERVER + "/api/tags/").json()

tags_names = []
tags_descs = []

for i in res_tags:
    tags_names.append(i["name"])
    tags_descs.append(i["description"] != None and i["title"] + ": " + i["description"] or i["title"])


# FETCH CONTENT WARNINGS

print("Fetching Content Warnings")

res_warn = requests.get(SERVER + "/api/content_warnings/").json()

warn_names = []
warn_descs = []

for i in res_warn:
    warn_names.append(i["name"])
    warn_descs.append(i["description"] != None and i["title"] + ": " + i["description"] or i["title"])


# UPDATE SCHEMAT

print("Updating Schema")

with open("cdb_schema.json", "r") as f:
    content = json.loads(f.read())

with open("cdb_schema.json", "w") as f:
    content["$defs"]["license"]["enum"] = licenses_names
    content["$defs"]["license"]["enumDescriptions"] = licenses_descs

    content["properties"]["tags"]["items"]["enum"] = tags_names
    content["properties"]["tags"]["items"]["enumDescriptions"] = tags_descs

    content["properties"]["content_warnings"]["items"]["enum"] = warn_names
    content["properties"]["content_warnings"]["items"]["enumDescriptions"] = warn_descs
    f.write(json.dumps(content, indent=2))
