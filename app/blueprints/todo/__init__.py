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

from celery import uuid
from flask import *
from flask_login import current_user, login_required
from sqlalchemy import or_, and_

from app.models import *
from app.querybuilder import QueryBuilder
from app.utils import get_int_or_abort, addNotification, addAuditLog, isYes
from app.tasks.importtasks import makeVCSRelease

bp = Blueprint("todo", __name__)

@bp.route("/todo/", methods=["GET", "POST"])
@login_required
def view_editor():
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
			return redirect(url_for("todo.view_editor"))
		else:
			abort(400)

	license_needed = Package.query \
		.filter(Package.state.in_([PackageState.READY_FOR_REVIEW, PackageState.APPROVED])) \
		.filter(or_(Package.license.has(License.name.like("Other %")),
			Package.media_license.has(License.name.like("Other %")))) \
		.all()

	total_packages = Package.query.filter_by(state=PackageState.APPROVED).count()
	total_to_tag = Package.query.filter_by(state=PackageState.APPROVED, tags=None).count()

	unfulfilled_meta_packages = MetaPackage.query \
			.filter(~ MetaPackage.packages.any(state=PackageState.APPROVED)) \
			.filter(MetaPackage.dependencies.any(Dependency.depender.has(state=PackageState.APPROVED), optional=False)) \
			.order_by(db.asc(MetaPackage.name)).count()

	return render_template("todo/editor.html", current_tab="editor",
			packages=packages, wip_packages=wip_packages, releases=releases, screenshots=screenshots,
			canApproveNew=canApproveNew, canApproveRel=canApproveRel, canApproveScn=canApproveScn,
			license_needed=license_needed, total_packages=total_packages, total_to_tag=total_to_tag,
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
	if num > 100 and not current_user.rank.atLeast(UserRank.APPROVER):
		num = 100

	query = query.paginate(page, num, True)
	next_url = url_for("todo.topics", page=query.next_num, query=qb.search,
			show_discarded=qb.show_discarded, n=num, sort=qb.order_by) \
			if query.has_next else None
	prev_url = url_for("todo.topics", page=query.prev_num, query=qb.search,
			show_discarded=qb.show_discarded, n=num, sort=qb.order_by) \
			if query.has_prev else None

	return render_template("todo/topics.html", current_tab="topics", topics=query.items, total=total,
			topic_count=topic_count, query=qb.search, show_discarded=qb.show_discarded,
			next_url=next_url, prev_url=prev_url, page=page, page_max=query.pages,
			n=num, sort_by=qb.order_by)


@bp.route("/todo/tags/")
@login_required
def tags():
	qb    = QueryBuilder(request.args)
	qb.setSortIfNone("score", "desc")
	query = qb.buildPackageQuery()

	only_no_tags = isYes(request.args.get("no_tags"))
	if only_no_tags:
		query = query.filter(Package.tags==None)

	tags = Tag.query.order_by(db.asc(Tag.title)).all()

	return render_template("todo/tags.html", current_tab="tags", packages=query.all(), \
			tags=tags, only_no_tags=only_no_tags)


@bp.route("/user/tags/")
def tags_user():
	return redirect(url_for('todo.tags', author=current_user.username))


@bp.route("/todo/metapackages/")
@login_required
def metapackages():
	mpackages = MetaPackage.query \
			.filter(~ MetaPackage.packages.any(state=PackageState.APPROVED)) \
			.filter(MetaPackage.dependencies.any(Dependency.depender.has(state=PackageState.APPROVED), optional=False)) \
			.order_by(db.asc(MetaPackage.name)).all()

	return render_template("todo/metapackages.html", mpackages=mpackages)


@bp.route("/user/todo/")
@bp.route("/users/<username>/todo/")
@login_required
def view_user(username=None):
	if username is None:
		return redirect(url_for("todo.view_user", username=current_user.username))

	user : User = User.query.filter_by(username=username).first()
	if not user:
		abort(404)

	if current_user != user and not current_user.rank.atLeast(UserRank.APPROVER):
		abort(403)

	unapproved_packages = user.packages \
		.filter(or_(Package.state == PackageState.WIP,
			Package.state == PackageState.CHANGES_NEEDED)) \
		.order_by(db.asc(Package.created_at)).all()

	packages_with_small_screenshots = user.maintained_packages \
		.filter(Package.screenshots.any(and_(PackageScreenshot.width < PackageScreenshot.SOFT_MIN_SIZE[0],
				PackageScreenshot.height < PackageScreenshot.SOFT_MIN_SIZE[1]))) \
		.all()

	outdated_packages = user.maintained_packages \
			.filter(Package.state != PackageState.DELETED,
					Package.update_config.has(PackageUpdateConfig.outdated_at.isnot(None))) \
			.order_by(db.asc(Package.title)).all()

	topics_to_add = ForumTopic.query \
			.filter_by(author_id=user.id) \
			.filter(~ db.exists().where(Package.forums == ForumTopic.topic_id)) \
			.order_by(db.asc(ForumTopic.name), db.asc(ForumTopic.title)) \
			.all()

	needs_tags = user.maintained_packages \
		.filter(Package.state != PackageState.DELETED, Package.tags==None) \
		.order_by(db.asc(Package.title)).all()

	return render_template("todo/user.html", current_tab="user", user=user,
			unapproved_packages=unapproved_packages, outdated_packages=outdated_packages,
			needs_tags=needs_tags, topics_to_add=topics_to_add,
			packages_with_small_screenshots=packages_with_small_screenshots,
			screenshot_min_size=PackageScreenshot.HARD_MIN_SIZE, screenshot_rec_size=PackageScreenshot.SOFT_MIN_SIZE)


@bp.route("/users/<username>/update-configs/apply-all/", methods=["POST"])
@login_required
def apply_all_updates(username):
	user: User = User.query.filter_by(username=username).first()
	if not user:
		abort(404)

	if current_user != user and not current_user.rank.atLeast(UserRank.EDITOR):
		abort(403)

	outdated_packages = user.maintained_packages \
		.filter(Package.state != PackageState.DELETED,
			Package.update_config.has(PackageUpdateConfig.outdated_at.isnot(None))) \
		.order_by(db.asc(Package.title)).all()

	for package in outdated_packages:
		if not package.checkPerm(current_user, Permission.MAKE_RELEASE):
			continue

		if package.releases.filter(or_(PackageRelease.task_id.isnot(None),
				PackageRelease.commit_hash==package.update_config.last_commit)).count() > 0:
			continue

		title = package.update_config.get_title()
		ref = package.update_config.get_ref()

		rel = PackageRelease()
		rel.package = package
		rel.title = title
		rel.url = ""
		rel.task_id = uuid()
		db.session.add(rel)
		db.session.commit()

		makeVCSRelease.apply_async((rel.id, ref),
				task_id=rel.task_id)

		msg = "Created release {} (Applied all Git Update Detection)".format(rel.title)
		addNotification(package.maintainers, current_user, NotificationType.PACKAGE_EDIT, msg,
				rel.getURL("packages.create_edit"), package)
		addAuditLog(AuditSeverity.NORMAL, current_user, msg, package.getURL("packages.view"), package)
		db.session.commit()

	return redirect(url_for("todo.view_user", username=username))


@bp.route("/todo/outdated/")
@login_required
def outdated():
	is_mtm_only = isYes(request.args.get("mtm"))

	query = db.session.query(Package).select_from(PackageUpdateConfig) \
			.filter(PackageUpdateConfig.outdated_at.isnot(None)) \
			.join(PackageUpdateConfig.package) \
			.filter(Package.state == PackageState.APPROVED)

	if is_mtm_only:
		query = query.filter(Package.repo.ilike("%github.com/minetest-mods/%"))

	sort_by = request.args.get("sort")
	if sort_by == "date":
		query = query.order_by(db.desc(PackageUpdateConfig.outdated_at))
	else:
		sort_by = "score"
		query = query.order_by(db.desc(Package.score))

	return render_template("todo/outdated.html", current_tab="outdated",
			outdated_packages=query.all(), sort_by=sort_by, is_mtm_only=is_mtm_only)
