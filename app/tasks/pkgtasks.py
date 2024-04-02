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

from sqlalchemy import or_, and_

from app.models import Package, db, PackageState
from app.tasks import celery
from app.utils import post_bot_message


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
			msg = "There's a ContentDB dialog redesign coming to Minetest 5.9.0. " \
					"Clicking a ContentDB link stays inside Minetest but an external repository / forums " \
					"link will open a web browser.\n\nYou should also remove dependency lists, as CDB already shows that.\n"

			for x in links:
				line = f"\n* {x[1]} -> {x[0].get_url('packages.view', absolute=True)}"
				line_added = msg + line
				if len(line_added) > 2000 - 150:
					post_bot_message(package, "You should link to ContentDB pages", msg)
					msg = f"(...continued)\n{line}"
				else:
					msg = line_added

			post_bot_message(package, "You should link to ContentDB pages", msg)

	db.session.commit()
