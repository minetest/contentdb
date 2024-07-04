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

import datetime
import re
from typing import Optional

import requests
from sqlalchemy import or_, and_

from app.markdown import get_links, render_markdown
from app.models import Package, db, PackageState, AuditLogEntry
from app.tasks import celery, TaskError
from app.utils import post_bot_message, post_to_approval_thread, get_system_user


@celery.task()
def update_package_scores():
	Package.query.update({ "score_downloads": Package.score_downloads * 0.93 })
	db.session.commit()

	for package in Package.query.all():
		package.recalculate_score()

	db.session.commit()


def desc_contains(desc: str, search_str: str):
	if search_str.startswith("https://forum.minetest.net/viewtopic.php?%t="):
		reg = re.compile(search_str.replace(".", "\\.").replace("/", "\\/").replace("?", "\\?").replace("%", ".*"))
		return reg.search(desc)
	else:
		return search_str in desc


@celery.task()
def notify_about_git_forum_links():
	package_links = [(x[0], x[1]) for x in db.session.query(Package, Package.repo)
		.filter(Package.repo.is_not(None), Package.state == PackageState.APPROVED).all()]
	for pair in db.session.query(Package, Package.forums) \
			.filter(Package.forums.is_not(None), Package.state == PackageState.APPROVED).all():
		package_links.append((pair[0], f"https://forum.minetest.net/viewtopic.php?%t={pair[1]}"))

	clauses = [and_(Package.id != pair[0].id, Package.desc.ilike(f"%{pair[1]}%")) for pair in package_links]
	packages = Package.query.filter(Package.desc != "", Package.desc.is_not(None), Package.state == PackageState.APPROVED, or_(*clauses)).all()

	for package in packages:
		links = []

		for (link_package, link) in package_links:
			if link_package != package and desc_contains(package.desc.lower(), link.lower()):
				links.append((link_package, link))

		if len(links) > 0:
			title = "You should link to ContentDB pages instead of repos/forum topics"
			msg = "You should update your long description to link to ContentDB pages instead of repositories or " \
					"forum topics, where possible.  \n" \
					"You should also remove lists of dependencies, as CDB already shows that.\n\n" \
					"There's a ContentDB dialog redesign coming to Minetest 5.9.0. " \
					"Clicking a ContentDB link stays inside Minetest but an external repository / forums " \
					"link will open a web browser. Therefore, linking to ContentDB pages when referring to a " \
					"package will improve the user experience.\n\nHere are some URLs you might wish to replace:\n"

			for x in links:
				line = f"\n* {x[1].replace('%', '')} -> {x[0].get_url('packages.view', absolute=True)}"
				line_added = msg + line
				if len(line_added) > 2000 - 150:
					post_bot_message(package, title, msg)
					msg = f"(...continued)\n{line}"
				else:
					msg = line_added

			post_bot_message(package, title, msg)

	db.session.commit()


@celery.task()
def clear_removed_packages(all_packages: bool):
	if all_packages:
		query = Package.query.filter_by(state=PackageState.DELETED)
	else:
		one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
		query = Package.query.filter(
			Package.state == PackageState.DELETED,
			Package.downloads < 1000,
			~Package.audit_log_entries.any(AuditLogEntry.created_at > one_year_ago))

	count = query.count()
	for pkg in query.all():
		pkg.review_thread = None
		db.session.delete(pkg)
	db.session.commit()

	return f"Deleted {count} soft deleted packages packages"


def _url_exists(url: str) -> bool:
	try:
		with requests.get(url, stream=True) as response:
			try:
				response.raise_for_status()
				return True
			except requests.exceptions.HTTPError:
				return False
	except requests.exceptions.ConnectionError:
		return False


def check_for_dead_links(package: Package) -> set[str]:
	links: list[Optional[str]] = [
		package.repo,
		package.website,
		package.issueTracker,
		package.forums_url,
		package.video_url,
		package.donate_url_actual,
		package.translation_url,
	]

	if package.desc:
		links.extend(get_links(render_markdown(package.desc), package.get_url("packages.view", absolute=True)))

	bad_urls = set()

	for link in links:
		if link is None:
			continue

		if not _url_exists(link):
			bad_urls.add(link)

	return bad_urls


@celery.task()
def check_package_on_submit(package_id: int):
	package = Package.query.get(package_id)
	if package is None:
		raise TaskError("No such package")

	bad_urls = check_for_dead_links(package)
	if len(bad_urls) > 0:
		marked = f"Marked {package.title} as Changed Needed"
		msg = "The following broken links were found on your package:\n\n" + "\n".join([f"- {x}" for x in bad_urls])

		system_user = get_system_user()
		post_to_approval_thread(package, system_user, marked, is_status_update=True, create_thread=True)
		post_to_approval_thread(package, system_user, msg, is_status_update=False, create_thread=True)
		package.state = PackageState.CHANGES_NEEDED
		db.session.commit()
