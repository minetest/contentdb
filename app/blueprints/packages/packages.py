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


from urllib.parse import quote as urlescape

from flask import render_template
from flask_babel import lazy_gettext, gettext
from flask_wtf import FlaskForm
from flask_login import login_required
from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload, subqueryload
from wtforms import *
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms.validators import *

from app.querybuilder import QueryBuilder
from app.rediscache import has_key, set_key
from app.tasks.importtasks import importRepoScreenshot
from app.utils import *
from . import bp, get_package_tabs
from app.logic.LogicError import LogicError
from app.logic.packages import do_edit_package
from app.models.packages import PackageProvides
from app.tasks.webhooktasks import post_discord_webhook


@bp.route("/packages/")
def list_all():
	qb    = QueryBuilder(request.args)
	query = qb.buildPackageQuery()
	title = qb.title

	query = query.options(
			joinedload(Package.license),
			joinedload(Package.media_license),
			subqueryload(Package.tags))

	ip = request.headers.get("X-Forwarded-For") or request.remote_addr
	if ip is not None and not is_user_bot():
		edited = False
		for tag in qb.tags:
			edited = True
			key = "tag/{}/{}".format(ip, tag.name)
			if not has_key(key):
				set_key(key, "true")
				Tag.query.filter_by(id=tag.id).update({
						"views": Tag.views + 1
					})

		if edited:
			db.session.commit()

	if qb.lucky:
		package = query.first()
		if package:
			return redirect(package.getURL("packages.view"))

		topic = qb.buildTopicQuery().first()
		if qb.search and topic:
			return redirect("https://forum.minetest.net/viewtopic.php?t=" + str(topic.topic_id))

	page  = get_int_or_abort(request.args.get("page"), 1)
	num   = min(40, get_int_or_abort(request.args.get("n"), 100))
	query = query.paginate(page, num, True)

	search = request.args.get("q")
	type_name = request.args.get("type")

	authors = []
	if search:
		authors = User.query \
			.filter(or_(*[func.lower(User.username) == name.lower().strip() for name in search.split(" ")])) \
			.all()

		authors = [(author.username, search.lower().replace(author.username.lower(), "")) for author in authors]

	topics = None
	if qb.search and not query.has_next:
		qb.show_discarded = True
		topics = qb.buildTopicQuery().all()

	tags_query = db.session.query(func.count(Tags.c.tag_id), Tag) \
  		.select_from(Tag).join(Tags).join(Package).group_by(Tag.id).order_by(db.asc(Tag.title))
	tags = qb.filterPackageQuery(tags_query).all()

	selected_tags = set(qb.tags)

	return render_template("packages/list.html",
			query_hint=title, packages=query.items, pagination=query,
			query=search, tags=tags, selected_tags=selected_tags, type=type_name,
			authors=authors, packages_count=query.total, topics=topics)


def getReleases(package):
	if package.checkPerm(current_user, Permission.MAKE_RELEASE):
		return package.releases.limit(5)
	else:
		return package.releases.filter_by(approved=True).limit(5)


@bp.route("/packages/<author>/<name>/")
@is_package_page
def view(package):
	show_similar = not package.approved and (
			current_user in package.maintainers or
				package.checkPerm(current_user, Permission.APPROVE_NEW))

	conflicting_modnames = None
	if show_similar and package.type != PackageType.TXP:
		conflicting_modnames = db.session.query(MetaPackage.name) \
				.filter(MetaPackage.id.in_([ mp.id for mp in package.provides ])) \
				.filter(MetaPackage.packages.any(Package.id != package.id)) \
				.all()

		conflicting_modnames += db.session.query(ForumTopic.name) \
				.filter(ForumTopic.name.in_([ mp.name for mp in package.provides ])) \
				.filter(ForumTopic.topic_id != package.forums) \
				.filter(~ db.exists().where(Package.forums==ForumTopic.topic_id)) \
				.order_by(db.asc(ForumTopic.name), db.asc(ForumTopic.title)) \
				.all()

		conflicting_modnames = set([x[0] for x in conflicting_modnames])

	packages_uses = None
	if package.type == PackageType.MOD:
		packages_uses = Package.query.filter(
				Package.type == PackageType.MOD,
				Package.id != package.id,
				Package.state != PackageState.DELETED,
				Package.dependencies.any(
						Dependency.meta_package_id.in_([p.id for p in package.provides]))) \
			.order_by(db.desc(Package.score)).limit(6).all()

	releases = getReleases(package)

	review_thread = package.review_thread
	if review_thread is not None and not review_thread.checkPerm(current_user, Permission.SEE_THREAD):
		review_thread = None

	topic_error = None
	topic_error_lvl = "warning"
	if package.state != PackageState.APPROVED and package.forums is not None:
		errors = []
		if Package.query.filter(Package.forums==package.forums, Package.state!=PackageState.DELETED).count() > 1:
			errors.append("<b>" + gettext("Error: Another package already uses this forum topic!") + "</b>")
			topic_error_lvl = "danger"

		topic = ForumTopic.query.get(package.forums)
		if topic is not None:
			if topic.author != package.author:
				errors.append("<b>" + gettext("Error: Forum topic author doesn't match package author.") + "</b>")
				topic_error_lvl = "danger"
		elif package.type != PackageType.TXP:
			errors.append(gettext("Warning: Forum topic not found. This may happen if the topic has only just been created."))

		topic_error = "<br />".join(errors)


	threads = Thread.query.filter_by(package_id=package.id, review_id=None)
	if not current_user.is_authenticated:
		threads = threads.filter_by(private=False)
	elif not current_user.rank.atLeast(UserRank.APPROVER) and not current_user == package.author:
		threads = threads.filter(or_(Thread.private == False, Thread.author == current_user))

	has_review = current_user.is_authenticated and PackageReview.query.filter_by(package=package, author=current_user).count() > 0

	return render_template("packages/view.html",
			package=package, releases=releases, packages_uses=packages_uses,
			conflicting_modnames=conflicting_modnames,
			review_thread=review_thread, topic_error=topic_error, topic_error_lvl=topic_error_lvl,
			threads=threads.all(), has_review=has_review)


@bp.route("/packages/<author>/<name>/shields/<type>/")
@is_package_page
def shield(package, type):
	if type == "title":
		url = "https://img.shields.io/static/v1?label=ContentDB&message={}&color={}" \
			.format(urlescape(package.title), urlescape("#375a7f"))
	elif type == "downloads":
		#api_url = abs_url_for("api.package", author=package.author.username, name=package.name)
		api_url = "https://content.minetest.net" + url_for("api.package", author=package.author.username, name=package.name)
		url = "https://img.shields.io/badge/dynamic/json?color={}&label=ContentDB&query=downloads&suffix=+downloads&url={}" \
			.format(urlescape("#375a7f"), urlescape(api_url))
	else:
		abort(404)

	return redirect(url)


@bp.route("/packages/<author>/<name>/download/")
@is_package_page
def download(package):
	release = package.getDownloadRelease()

	if release is None:
		if "application/zip" in request.accept_mimetypes and \
				not "text/html" in request.accept_mimetypes:
			return "", 204
		else:
			flash(gettext("No download available."), "danger")
			return redirect(package.getURL("packages.view"))
	else:
		return redirect(release.getDownloadURL())


def makeLabel(obj):
	if obj.description:
		return "{}: {}".format(obj.title, obj.description)
	else:
		return obj.title


class PackageForm(FlaskForm):
	type             = SelectField(lazy_gettext("Type"), [InputRequired()], choices=PackageType.choices(), coerce=PackageType.coerce, default=PackageType.MOD)
	title            = StringField(lazy_gettext("Title (Human-readable)"), [InputRequired(), Length(1, 100)])
	name             = StringField(lazy_gettext("Name (Technical)"), [InputRequired(), Length(1, 100), Regexp("^[a-z0-9_]+$", 0, lazy_gettext("Lower case letters (a-z), digits (0-9), and underscores (_) only"))])
	short_desc       = StringField(lazy_gettext("Short Description (Plaintext)"), [InputRequired(), Length(1,200)])

	dev_state        = SelectField(lazy_gettext("Maintenance State"), [InputRequired()], choices=PackageDevState.choices(with_none=True), coerce=PackageDevState.coerce)

	tags             = QuerySelectMultipleField(lazy_gettext('Tags'), query_factory=lambda: Tag.query.order_by(db.asc(Tag.name)), get_pk=lambda a: a.id, get_label=makeLabel)
	content_warnings = QuerySelectMultipleField(lazy_gettext('Content Warnings'), query_factory=lambda: ContentWarning.query.order_by(db.asc(ContentWarning.name)), get_pk=lambda a: a.id, get_label=makeLabel)
	license          = QuerySelectField(lazy_gettext("License"), [DataRequired()], allow_blank=True, query_factory=lambda: License.query.order_by(db.asc(License.name)), get_pk=lambda a: a.id, get_label=lambda a: a.name)
	media_license    = QuerySelectField(lazy_gettext("Media License"), [DataRequired()], allow_blank=True, query_factory=lambda: License.query.order_by(db.asc(License.name)), get_pk=lambda a: a.id, get_label=lambda a: a.name)

	desc             = TextAreaField(lazy_gettext("Long Description (Markdown)"), [Optional(), Length(0,10000)])

	repo             = StringField(lazy_gettext("VCS Repository URL"), [Optional(), URL()], filters = [lambda x: x or None])
	website          = StringField(lazy_gettext("Website URL"), [Optional(), URL()], filters = [lambda x: x or None])
	issueTracker     = StringField(lazy_gettext("Issue Tracker URL"), [Optional(), URL()], filters = [lambda x: x or None])
	forums           = IntegerField(lazy_gettext("Forum Topic ID"), [Optional(), NumberRange(0,999999)])

	submit           = SubmitField(lazy_gettext("Save"))


@bp.route("/packages/new/", methods=["GET", "POST"])
@bp.route("/packages/<author>/<name>/edit/", methods=["GET", "POST"])
@login_required
def create_edit(author=None, name=None):
	package = None
	if author is None:
		form = PackageForm(formdata=request.form)
		author = request.args.get("author")
		if author is None or author == current_user.username:
			author = current_user
		else:
			author = User.query.filter_by(username=author).first()
			if author is None:
				flash(gettext("Unable to find that user"), "danger")
				return redirect(url_for("packages.create_edit"))

			if not author.checkPerm(current_user, Permission.CHANGE_AUTHOR):
				flash(gettext("Permission denied"), "danger")
				return redirect(url_for("packages.create_edit"))

	else:
		package = getPackageByInfo(author, name)
		if package is None:
			abort(404)
		if not package.checkPerm(current_user, Permission.EDIT_PACKAGE):
			return redirect(package.getURL("packages.view"))

		author = package.author

		form = PackageForm(formdata=request.form, obj=package)

	# Initial form class from post data and default data
	if request.method == "GET":
		if package is None:
			form.name.data   = request.args.get("bname")
			form.title.data  = request.args.get("title")
			form.repo.data   = request.args.get("repo")
			form.forums.data = request.args.get("forums")
			form.license.data = None
			form.media_license.data = None
		else:
			form.tags.data         = list(package.tags)
			form.content_warnings.data = list(package.content_warnings)

	if request.method == "POST" and form.type.data == PackageType.TXP:
		form.license.data = form.media_license.data

	if form.validate_on_submit():
		wasNew = False
		if not package:
			package = Package.query.filter_by(name=form["name"].data, author_id=author.id).first()
			if package is not None:
				if package.state == PackageState.READY_FOR_REVIEW:
					Package.query.filter_by(name=form["name"].data, author_id=author.id).delete()
				else:
					flash(gettext("Package already exists!"), "danger")
					return redirect(url_for("packages.create_edit"))

			package = Package()
			package.author = author
			package.maintainers.append(author)
			wasNew = True

		try:
			do_edit_package(current_user, package, wasNew, True, {
				"type": form.type.data,
				"title": form.title.data,
				"name": form.name.data,
				"short_desc": form.short_desc.data,
				"dev_state": form.dev_state.data,
				"tags": form.tags.raw_data,
				"content_warnings": form.content_warnings.raw_data,
				"license": form.license.data,
				"media_license": form.media_license.data,
				"desc": form.desc.data,
				"repo": form.repo.data,
				"website": form.website.data,
				"issueTracker": form.issueTracker.data,
				"forums": form.forums.data,
			})

			if wasNew and package.repo is not None:
				importRepoScreenshot.delay(package.id)

			next_url = package.getURL("packages.view")
			if wasNew and ("WTFPL" in package.license.name or "WTFPL" in package.media_license.name):
				next_url = url_for("flatpage", path="help/wtfpl", r=next_url)
			elif wasNew:
				next_url = package.getURL("packages.setup_releases")

			return redirect(next_url)
		except LogicError as e:
			flash(e.message, "danger")

	package_query = Package.query.filter_by(state=PackageState.APPROVED)
	if package is not None:
		package_query = package_query.filter(Package.id != package.id)

	enableWizard = name is None and request.method != "POST"
	return render_template("packages/create_edit.html", package=package,
			form=form, author=author, enable_wizard=enableWizard,
			packages=package_query.all(),
			mpackages=MetaPackage.query.order_by(db.asc(MetaPackage.name)).all(),
			tabs=get_package_tabs(current_user, package), current_tab="edit")


@bp.route("/packages/<author>/<name>/state/", methods=["POST"])
@login_required
@is_package_page
def move_to_state(package):
	state = PackageState.get(request.args.get("state"))
	if state is None:
		abort(400)

	if not package.canMoveToState(current_user, state):
		flash(gettext("You don't have permission to do that"), "danger")
		return redirect(package.getURL("packages.view"))

	package.state = state
	msg = "Marked {} as {}".format(package.title, state.value)

	if state == PackageState.APPROVED:
		if not package.approved_at:
			post_discord_webhook.delay(package.author.username,
					"New package {}".format(package.getURL("packages.view", absolute=True)), False)
			package.approved_at = datetime.datetime.now()

		screenshots = PackageScreenshot.query.filter_by(package=package, approved=False).all()
		for s in screenshots:
			s.approved = True

		msg = "Approved {}".format(package.title)
	elif state == PackageState.READY_FOR_REVIEW:
		post_discord_webhook.delay(package.author.username,
				"Ready for Review: {}".format(package.getURL("packages.view", absolute=True)), True)

	addNotification(package.maintainers, current_user, NotificationType.PACKAGE_APPROVAL, msg, package.getURL("packages.view"), package)
	severity = AuditSeverity.NORMAL if current_user in package.maintainers else AuditSeverity.EDITOR
	addAuditLog(severity, current_user, msg, package.getURL("packages.view"), package)

	db.session.commit()

	if package.state == PackageState.CHANGES_NEEDED:
		flash(gettext("Please comment what changes are needed in the approval thread"), "warning")
		if package.review_thread:
			return redirect(package.review_thread.getViewURL())
		else:
			return redirect(url_for('threads.new', pid=package.id, title='Package approval comments'))

	return redirect(package.getURL("packages.view"))


@bp.route("/packages/<author>/<name>/remove/", methods=["GET", "POST"])
@login_required
@is_package_page
def remove(package):
	if request.method == "GET":
		return render_template("packages/remove.html", package=package,
				tabs=get_package_tabs(current_user, package), current_tab="remove")

	reason = request.form.get("reason") or "?"

	if "delete" in request.form:
		if not package.checkPerm(current_user, Permission.DELETE_PACKAGE):
			flash(gettext("You don't have permission to do that."), "danger")
			return redirect(package.getURL("packages.view"))

		package.state = PackageState.DELETED

		url = url_for("users.profile", username=package.author.username)
		msg = "Deleted {}, reason={}".format(package.title, reason)
		addNotification(package.maintainers, current_user, NotificationType.PACKAGE_EDIT, msg, url, package)
		addAuditLog(AuditSeverity.EDITOR, current_user, msg, url)
		db.session.commit()

		flash(gettext("Deleted package"), "success")

		return redirect(url)
	elif "unapprove" in request.form:
		if not package.checkPerm(current_user, Permission.UNAPPROVE_PACKAGE):
			flash(gettext("You don't have permission to do that."), "danger")
			return redirect(package.getURL("packages.view"))

		package.state = PackageState.WIP

		msg = "Unapproved {}, reason={}".format(package.title, reason)
		addNotification(package.maintainers, current_user, NotificationType.PACKAGE_APPROVAL, msg, package.getURL("packages.view"), package)
		addAuditLog(AuditSeverity.EDITOR, current_user, msg, package.getURL("packages.view"), package)

		db.session.commit()

		flash(gettext("Unapproved package"), "success")

		return redirect(package.getURL("packages.view"))
	else:
		abort(400)



class PackageMaintainersForm(FlaskForm):
	maintainers_str  = StringField(lazy_gettext("Maintainers (Comma-separated)"), [Optional()])
	submit	      = SubmitField(lazy_gettext("Save"))


@bp.route("/packages/<author>/<name>/edit-maintainers/", methods=["GET", "POST"])
@login_required
@is_package_page
def edit_maintainers(package):
	if not package.checkPerm(current_user, Permission.EDIT_MAINTAINERS):
		flash(gettext("You do not have permission to edit maintainers"), "danger")
		return redirect(package.getURL("packages.view"))

	form = PackageMaintainersForm(formdata=request.form)
	if request.method == "GET":
		form.maintainers_str.data = ", ".join([ x.username for x in package.maintainers if x != package.author ])

	if form.validate_on_submit():
		usernames = [x.strip().lower() for x in form.maintainers_str.data.split(",")]
		users = User.query.filter(func.lower(User.username).in_(usernames)).all()

		thread = package.threads.filter_by(author=get_system_user()).first()

		for user in users:
			if not user in package.maintainers:
				if thread:
					thread.watchers.append(user)
				addNotification(user, current_user, NotificationType.MAINTAINER,
						"Added you as a maintainer of {}".format(package.title), package.getURL("packages.view"), package)

		for user in package.maintainers:
			if user != package.author and not user in users:
				addNotification(user, current_user, NotificationType.MAINTAINER,
						"Removed you as a maintainer of {}".format(package.title), package.getURL("packages.view"), package)

		package.maintainers.clear()
		package.maintainers.extend(users)
		if package.author not in package.maintainers:
			package.maintainers.append(package.author)

		msg = "Edited {} maintainers".format(package.title)
		addNotification(package.author, current_user, NotificationType.MAINTAINER, msg, package.getURL("packages.view"), package)
		severity = AuditSeverity.NORMAL if current_user == package.author else AuditSeverity.MODERATION
		addAuditLog(severity, current_user, msg, package.getURL("packages.view"), package)

		db.session.commit()

		return redirect(package.getURL("packages.view"))

	users = User.query.filter(User.rank >= UserRank.NEW_MEMBER).order_by(db.asc(User.username)).all()

	return render_template("packages/edit_maintainers.html", package=package, form=form,
			users=users, tabs=get_package_tabs(current_user, package), current_tab="maintainers")


@bp.route("/packages/<author>/<name>/remove-self-maintainer/", methods=["POST"])
@login_required
@is_package_page
def remove_self_maintainers(package):
	if not current_user in package.maintainers:
		flash(gettext("You are not a maintainer"), "danger")

	elif current_user == package.author:
		flash(gettext("Package owners cannot remove themselves as maintainers"), "danger")

	else:
		package.maintainers.remove(current_user)

		addNotification(package.author, current_user, NotificationType.MAINTAINER,
				"Removed themself as a maintainer of {}".format(package.title), package.getURL("packages.view"), package)

		db.session.commit()

	return redirect(package.getURL("packages.view"))


@bp.route("/packages/<author>/<name>/audit/")
@login_required
@is_package_page
def audit(package):
	if not (package.checkPerm(current_user, Permission.EDIT_PACKAGE) or
			package.checkPerm(current_user, Permission.APPROVE_NEW)):
		abort(403)

	page = get_int_or_abort(request.args.get("page"), 1)
	num = min(40, get_int_or_abort(request.args.get("n"), 100))

	query = package.audit_log_entries.order_by(db.desc(AuditLogEntry.created_at))

	pagination = query.paginate(page, num, True)
	return render_template("packages/audit.html", log=pagination.items, pagination=pagination,
		package=package, tabs=get_package_tabs(current_user, package), current_tab="audit")


class PackageAliasForm(FlaskForm):
	author  = StringField(lazy_gettext("Author Name"), [InputRequired(), Length(1, 50)])
	name    = StringField(lazy_gettext("Name (Technical)"), [InputRequired(), Length(1, 100),
			Regexp("^[a-z0-9_]+$", 0, lazy_gettext("Lower case letters (a-z), digits (0-9), and underscores (_) only"))])
	submit  = SubmitField(lazy_gettext("Save"))


@bp.route("/packages/<author>/<name>/aliases/")
@rank_required(UserRank.EDITOR)
@is_package_page
def alias_list(package: Package):
	return render_template("packages/alias_list.html", package=package)


@bp.route("/packages/<author>/<name>/aliases/new/", methods=["GET", "POST"])
@bp.route("/packages/<author>/<name>/aliases/<int:alias_id>/", methods=["GET", "POST"])
@rank_required(UserRank.EDITOR)
@is_package_page
def alias_create_edit(package: Package, alias_id: int = None):
	alias = None
	if alias_id:
		alias = PackageAlias.query.get(alias_id)
		if alias is None or alias.package != package:
			abort(404)

	form = PackageAliasForm(request.form, obj=alias)
	if form.validate_on_submit():
		if alias is None:
			alias = PackageAlias()
			alias.package = package
			db.session.add(alias)

		form.populate_obj(alias)
		db.session.commit()

		return redirect(package.getURL("packages.alias_list"))

	return render_template("packages/alias_create_edit.html", package=package, form=form)


@bp.route("/packages/<author>/<name>/share/")
@login_required
@is_package_page
def share(package):
	return render_template("packages/share.html", package=package,
			tabs=get_package_tabs(current_user, package), current_tab="share")


@bp.route("/packages/<author>/<name>/similar/")
@is_package_page
def similar(package):
	packages_modnames = {}
	for metapackage in package.provides:
		packages_modnames[metapackage] = Package.query.filter(Package.id != package.id,
				Package.state != PackageState.DELETED) \
			.filter(Package.provides.any(PackageProvides.c.metapackage_id == metapackage.id)) \
			.order_by(db.desc(Package.score)) \
			.all()

	similar_topics = ForumTopic.query \
		.filter_by(name=package.name) \
		.filter(ForumTopic.topic_id != package.forums) \
		.filter(~ db.exists().where(Package.forums == ForumTopic.topic_id)) \
		.order_by(db.asc(ForumTopic.name), db.asc(ForumTopic.title)) \
		.all()

	return render_template("packages/similar.html", package=package,
			packages_modnames=packages_modnames, similar_topics=similar_topics)
