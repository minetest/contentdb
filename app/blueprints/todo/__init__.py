# ContentDB
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
from app.models import *
from app.querybuilder import QueryBuilder
from app.utils import get_int_or_abort
from sqlalchemy import or_

bp = Blueprint("todo", __name__)

@bp.route("/todo/", methods=["GET", "POST"])
@login_required
def view():
	canApproveNew = Permission.APPROVE_NEW.check(current_user)
	canApproveRel = Permission.APPROVE_RELEASE.check(current_user)
	canApproveScn = Permission.APPROVE_SCREENSHOT.check(current_user)

	packages = None
	wip_packages = None
	if canApproveNew:
		packages = Package.query.filter_by(state=PackageState.READY_FOR_REVIEW) \
			.order_by(db.desc(Package.created_at)).all()
		wip_packages = Package.query.filter(or_(Package.state==PackageState.WIP, Package.state==PackageState.CHANGES_NEEDED)) \
			.order_by(db.desc(Package.created_at)).all()

	releases = None
	if canApproveRel:
		releases = PackageRelease.query.filter_by(approved=False).all()

	screenshots = None
	if canApproveScn:
		screenshots = PackageScreenshot.query.filter_by(approved=False).all()

	if not canApproveNew and not canApproveRel and not canApproveScn:
		abort(403)

	if request.method == "POST":
		if request.form["action"] == "screenshots_approve_all":
			if not canApproveScn:
				abort(403)

			PackageScreenshot.query.update({ "approved": True })
			db.session.commit()
			return redirect(url_for("todo.view"))
		else:
			abort(400)

	topic_query = ForumTopic.query \
			.filter_by(discarded=False)

	total_topics = topic_query.count()
	topics_to_add = topic_query \
			.filter(~ db.exists().where(Package.forums==ForumTopic.topic_id)) \
			.count()

	total_packages = Package.query.filter_by(state=PackageState.APPROVED).count()
	total_to_tag = Package.query.filter_by(state=PackageState.APPROVED, tags=None).count()

	unfulfilled_meta_packages = MetaPackage.query \
			.filter(~ MetaPackage.packages.any(state=PackageState.APPROVED)) \
			.filter(MetaPackage.dependencies.any(optional=False)) \
			.order_by(db.asc(MetaPackage.name)).count()

	return render_template("todo/list.html", title="Reports and Work Queue",
		packages=packages, wip_packages=wip_packages, releases=releases, screenshots=screenshots,
		canApproveNew=canApproveNew, canApproveRel=canApproveRel, canApproveScn=canApproveScn,
		topics_to_add=topics_to_add, total_topics=total_topics, \
		total_packages=total_packages, total_to_tag=total_to_tag, \
		unfulfilled_meta_packages=unfulfilled_meta_packages)


@bp.route("/todo/topics/")
@login_required
def topics():
	qb    = QueryBuilder(request.args)
	qb.setSortIfNone("date")
	query = qb.buildTopicQuery()

	tmp_q = ForumTopic.query
	if not qb.show_discarded:
		tmp_q = tmp_q.filter_by(discarded=False)
	total = tmp_q.count()
	topic_count = query.count()

	page  = get_int_or_abort(request.args.get("page"), 1)
	num   = get_int_or_abort(request.args.get("n"), 100)
	if num > 100 and not current_user.rank.atLeast(UserRank.EDITOR):
		num = 100

	query = query.paginate(page, num, True)
	next_url = url_for("todo.topics", page=query.next_num, query=qb.search, \
	 	show_discarded=qb.show_discarded, n=num, sort=qb.order_by) \
			if query.has_next else None
	prev_url = url_for("todo.topics", page=query.prev_num, query=qb.search, \
	 	show_discarded=qb.show_discarded, n=num, sort=qb.order_by) \
			if query.has_prev else None

	return render_template("todo/topics.html", topics=query.items, total=total, \
			topic_count=topic_count, query=qb.search, show_discarded=qb.show_discarded, \
			next_url=next_url, prev_url=prev_url, page=page, page_max=query.pages, \
			n=num, sort_by=qb.order_by)


@bp.route("/todo/tags/")
@login_required
def tags():
	qb    = QueryBuilder(request.args)
	qb.setSortIfNone("score", "desc")
	query = qb.buildPackageQuery()

	tags = Tag.query.order_by(db.asc(Tag.title)).all()

	return render_template("todo/tags.html", packages=query.all(), tags=tags)


@bp.route("/todo/metapackages/")
@login_required
def metapackages():
	mpackages = MetaPackage.query \
			.filter(~ MetaPackage.packages.any(state=PackageState.APPROVED)) \
			.filter(MetaPackage.dependencies.any(optional=False)) \
			.order_by(db.asc(MetaPackage.name)).all()

	return render_template("todo/metapackages.html", mpackages=mpackages)
