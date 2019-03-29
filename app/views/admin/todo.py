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


from flask import *
from flask_user import *
import flask_menu as menu
from app import app
from app.models import *
from app.querybuilder import QueryBuilder

@app.route("/todo/")
@login_required
def todo_page():
	canApproveNew = Permission.APPROVE_NEW.check(current_user)
	canApproveRel = Permission.APPROVE_RELEASE.check(current_user)
	canApproveScn = Permission.APPROVE_SCREENSHOT.check(current_user)

	packages = None
	if canApproveNew:
		packages = Package.query.filter_by(approved=False, soft_deleted=False).all()

	releases = None
	if canApproveRel:
		releases = PackageRelease.query.filter_by(approved=False).all()

	screenshots = None
	if canApproveScn:
		screenshots = PackageScreenshot.query.filter_by(approved=False).all()


	topics_to_add = ForumTopic.query \
			.filter(~ db.exists().where(Package.forums==ForumTopic.topic_id)) \
			.filter_by(discarded=False) \
			.count()

	return render_template("todo/list.html", title="Reports and Work Queue",
		packages=packages, releases=releases, screenshots=screenshots,
		canApproveNew=canApproveNew, canApproveRel=canApproveRel, canApproveScn=canApproveScn,
		topics_to_add=topics_to_add)


@app.route("/todo/topics/")
@login_required
def todo_topics_page():
	qb    = QueryBuilder(request.args)
	qb.setSortIfNone("date")
	query = qb.buildTopicQuery()

	tmp_q = ForumTopic.query
	if not qb.show_discarded:
		tmp_q = tmp_q.filter_by(discarded=qb.show_discarded)
	total = tmp_q.count()
	topic_count = query.count()

	page  = int(request.args.get("page") or 1)
	num   = int(request.args.get("n") or 100)
	if num > 100 and not current_user.rank.atLeast(UserRank.EDITOR):
		num = 100

	query = query.paginate(page, num, True)
	next_url = url_for("todo_topics_page", page=query.next_num, query=qb.search, \
	 	show_discarded=qb.show_discarded, n=num, sort=qb.order_by) \
			if query.has_next else None
	prev_url = url_for("todo_topics_page", page=query.prev_num, query=qb.search, \
	 	show_discarded=qb.show_discarded, n=num, sort=qb.order_by) \
			if query.has_prev else None

	return render_template("todo/topics.html", topics=query.items, total=total, \
			topic_count=topic_count, query=qb.search, show_discarded=qb.show_discarded, \
			next_url=next_url, prev_url=prev_url, page=page, page_max=query.pages, \
			n=num, sort_by=qb.order_by)
