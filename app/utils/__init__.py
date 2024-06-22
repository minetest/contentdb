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

import re
import secrets
from typing import Dict

import deep_compare
from flask import current_app

from .flask import *
from .models import *
from .user import *

YESES = ["yes", "true", "1", "on"]


def is_username_valid(username: str) -> bool:
	return username is not None and len(username) >= 2 and \
			re.match(r"^[A-Za-z0-9._-]*$", username) and not re.match(r"^\.*$", username)


def make_valid_username(username: str) -> str:
	return re.sub(r"[^A-Za-z0-9._-]+", "_", username)


def is_yes(val):
	return val and val.lower() in YESES


def is_no(val):
	return val and not is_yes(val)


def nonempty_or_none(str):
	if str is None or str == "":
		return None

	return str


def should_return_json():
	return "application/json" in request.accept_mimetypes and \
			not "text/html" in request.accept_mimetypes


def random_string(n):
	return secrets.token_hex(int(n / 2))


def has_blocked_domains(text: str, username: str, location: str) -> bool:
	if text is None:
		return False

	blocked_domains = current_app.config["BLOCKED_DOMAINS"]
	for domain in blocked_domains:
		if domain in text:
			from app.tasks.webhooktasks import post_discord_webhook
			post_discord_webhook.delay(username,
					f"Attempted to post blocked domain {domain} in {location}",
					True)
			return True

	return False


def diff_dictionaries(one: Dict, two: Dict) -> List:
	if len(set(one.keys()).difference(set(two.keys()))) != 0:
		raise "Mismatching keys"

	retval = []

	for key, before in one.items():
		after = two[key]

		if isinstance(before, dict):
			diff = diff_dictionaries(before, after)
			if len(diff) != 0:
				retval.append({
					"key": key,
					"changes": diff,
				})
		elif not deep_compare.CompareVariables.compare(before, after):
			retval.append({
				"key": key,
				"before": before,
				"after": after,
			})

	return retval


def describe_difference(diff: List, available_space: int) -> typing.Optional[str]:
	if len(diff) == 0 or available_space <= 0:
		return None

	if len(diff) == 1 and "before" in diff[0] and "after" in diff[0]:
		key = diff[0]["key"]
		before = diff[0]["before"]
		after = diff[0]["after"]

		if isinstance(before, str) and isinstance(after, str):
			if len(before) + len(after) <= available_space + 30:
				return f"{key}: {before} -> {after}"

		elif isinstance(before, list) and isinstance(after, list):
			removed = []
			added = []
			for x in before:
				if x not in after:
					removed.append(x)
			for x in after:
				if x not in before:
					added.append(x)

			parts = ["-" + str(x) for x in removed] + ["+" + str(x) for x in added]
			return f"{key}: {', '.join(parts)}"

	return ", ".join([x["key"] for x in diff])
