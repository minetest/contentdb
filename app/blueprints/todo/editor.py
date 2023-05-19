# ContentDB
# Copyright (C) 2018-23 rubenwardy
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


from flask import redirect, url_for, abort, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.models import Package, PackageState, PackageScreenshot, PackageUpdateConfig, ForumTopic, db, \
	PackageRelease, Permission, UserRank, License, MetaPackage, Dependency, AuditLogEntry, Tag, MinetestRelease
from app.querybuilder import QueryBuilder
from app.utils import get_int_or_abort, isYes
from . import bp


@bp.route("/todo/", methods=["GET", "POST"])
@login_required
def view_editor():
	can_approve_new = Permission.APPROVE_NEW.check(current_user)
	can_approve_rel = Permission.APPROVE_RELEASE.check(current_user)
	can_approve_scn = Permission.APPROVE_SCREENSHOT.check(current_user)

	packages = None
	wip_packages = None
	if can_approve_new:
		packages = Package.query.filter_by(state=PackageState.READY_FOR_REVIEW) \
			.order_by(db.desc(Package.created_at)).all()
		wip_packages = Package.query \
			.filter(or_(Package.state == PackageState.WIP, Package.state == PackageState.CHANGES_NEEDED)) \
			.order_by(db.desc(Package.created_at)).all()

	releases = None
	if can_approve_rel:
		releases = PackageRelease.query.filter_by(approved=False).all()

	screenshots = None
	if can_approve_scn:
		screenshots = PackageScreenshot.query.filter_by(approved=False).all()

	if not can_approve_new and not can_approve_rel and not can_approve_scn:
		abort(403)

	if request.method == "POST":
		if request.form["action"] == "screenshots_approve_all":
			if not can_approve_scn:
				abort(403)

			PackageScreenshot.query.update({"approved": True})
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

	audit_log = AuditLogEntry.query \
		.filter(AuditLogEntry.package.has()) \
		.order_by(db.desc(AuditLogEntry.created_at)) \
		.limit(20).all()

	return render_template("todo/editor.html", current_tab="editor",
			packages=packages, wip_packages=wip_packages, releases=releases, screenshots=screenshots,
			canApproveNew=can_approve_new, canApproveRel=can_approve_rel, canApproveScn=can_approve_scn,
			license_needed=license_needed, total_packages=total_packages, total_to_tag=total_to_tag,
			unfulfilled_meta_packages=unfulfilled_meta_packages, audit_log=audit_log)


@bp.route("/todo/topics/")
@login_required
def topics():
	qb = QueryBuilder(request.args)
	qb.setSortIfNone("date")
	query = qb.buildTopicQuery()

	tmp_q = ForumTopic.query
	if not qb.show_discarded:
		tmp_q = tmp_q.filter_by(discarded=False)
	total = tmp_q.count()
	topic_count = query.count()

	page = get_int_or_abort(request.args.get("page"), 1)
	num = get_int_or_abort(request.args.get("n"), 100)
	if num > 100 and not current_user.rank.atLeast(UserRank.APPROVER):
		num = 100

	query = query.paginate(page=page, per_page=num)
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
		query = query.filter(Package.tags == None)

	tags = Tag.query.order_by(db.asc(Tag.title)).all()

	return render_template("todo/tags.html", current_tab="tags", packages=query.all(),
			tags=tags, only_no_tags=only_no_tags)


@bp.route("/todo/modnames/")
@login_required
def modnames():
	mnames = MetaPackage.query \
			.filter(~ MetaPackage.packages.any(state=PackageState.APPROVED)) \
			.filter(MetaPackage.dependencies.any(Dependency.depender.has(state=PackageState.APPROVED), optional=False)) \
			.order_by(db.asc(MetaPackage.name)).all()

	return render_template("todo/modnames.html", modnames=mnames)


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


@bp.route("/todo/screenshots/")
@login_required
def screenshots():
	is_mtm_only = isYes(request.args.get("mtm"))

	query = db.session.query(Package) \
			.filter(~Package.screenshots.any()) \
			.filter(Package.state == PackageState.APPROVED)

	if is_mtm_only:
		query = query.filter(Package.repo.ilike("%github.com/minetest-mods/%"))

	sort_by = request.args.get("sort")
	if sort_by == "date":
		query = query.order_by(db.desc(Package.approved_at))
	else:
		sort_by = "score"
		query = query.order_by(db.desc(Package.score))

	return render_template("todo/screenshots.html", current_tab="screenshots",
			packages=query.all(), sort_by=sort_by, is_mtm_only=is_mtm_only)


@bp.route("/todo/mtver_support/")
@login_required
def mtver_support():
	is_mtm_only = isYes(request.args.get("mtm"))

	current_stable = MinetestRelease.query.filter(~MinetestRelease.name.like("%-dev")).order_by(db.desc(MinetestRelease.id)).first()

	query = db.session.query(Package) \
			.filter(~Package.releases.any(or_(PackageRelease.max_rel==None, PackageRelease.max_rel == current_stable))) \
			.filter(Package.state == PackageState.APPROVED)

	if is_mtm_only:
		query = query.filter(Package.repo.ilike("%github.com/minetest-mods/%"))

	sort_by = request.args.get("sort")
	if sort_by == "date":
		query = query.order_by(db.desc(Package.approved_at))
	else:
		sort_by = "score"
		query = query.order_by(db.desc(Package.score))

	return render_template("todo/mtver_support.html", current_tab="screenshots",
			packages=query.all(), sort_by=sort_by, is_mtm_only=is_mtm_only, current_stable=current_stable)
