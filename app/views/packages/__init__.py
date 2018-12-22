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
from flask.ext import menu
from app import app
from app.models import *
from app.tasks.importtasks import importRepoScreenshot, makeVCSRelease

from app.utils import *

from celery import uuid
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from sqlalchemy import or_, any_


class QueryBuilder:
	title  = None
	types  = None
	search = None

	def __init__(self):
		title = "Packages"

		# Get request types
		types = request.args.getlist("type")
		types = [PackageType.get(tname) for tname in types]
		types = [type for type in types if type is not None]
		if len(types) > 0:
			title = ", ".join([type.value + "s" for type in types])

		self.title  = title
		self.types  = types
		self.search = request.args.get("q")
		self.lucky  = "lucky" in request.args
		self.hide_nonfree = isNo(request.args.get("nonfree"))
		self.limit  = 1 if self.lucky else None

	def buildPackageQuery(self):
		query = Package.query.filter_by(soft_deleted=False, approved=True)

		if len(self.types) > 0:
			query = query.filter(Package.type.in_(self.types))

		if self.search is not None and self.search.strip() != "":
			query = query.filter(Package.title.ilike('%' + self.search + '%'))

		query = query.order_by(db.desc(Package.score))

		if self.hide_nonfree:
			query = query.filter(Package.license.has(License.is_foss == True))
			query = query.filter(Package.media_license.has(License.is_foss == True))

		if self.limit:
			query = query.limit(self.limit)

		return query

	def buildTopicQuery(self):
		topics = ForumTopic.query \
				.filter(~ db.exists().where(Package.forums==ForumTopic.topic_id)) \
				.order_by(db.asc(ForumTopic.wip), db.asc(ForumTopic.name), db.asc(ForumTopic.title)) \
				.filter(ForumTopic.title.ilike('%' + self.search + '%'))

		if len(self.types) > 0:
			topics = topics.filter(ForumTopic.type.in_(self.types))

		if self.hide_nonfree:
			query = query.filter(Package.license.has(License.is_foss == True))
			query = query.filter(Package.media_license.has(License.is_foss == True))

		if self.limit:
			topics = topics.limit(self.limit)

		return topics

@menu.register_menu(app, ".mods", "Mods", order=11, endpoint_arguments_constructor=lambda: { 'type': 'mod' })
@menu.register_menu(app, ".games", "Games", order=12, endpoint_arguments_constructor=lambda: { 'type': 'game' })
@menu.register_menu(app, ".txp", "Texture Packs", order=13, endpoint_arguments_constructor=lambda: { 'type': 'txp' })
@app.route("/packages/")
def packages_page():
	if shouldReturnJson():
		return redirect(url_for("api_packages_page"))

	qb    = QueryBuilder()
	query = qb.buildPackageQuery()
	title = qb.title

	if qb.lucky:
		package = query.first()
		if package:
			return redirect(package.getDetailsURL())

		topic = qb.buildTopicQuery().first()
		if topic:
			return redirect("https://forum.minetest.net/viewtopic.php?t=" + str(topic.topic_id))

	page  = int(request.args.get("page") or 1)
	num   = min(42, int(request.args.get("n") or 100))
	query = query.paginate(page, num, True)

	search = request.args.get("q")
	type_name = request.args.get("type")

	next_url = url_for("packages_page", type=type_name, q=search, page=query.next_num) \
			if query.has_next else None
	prev_url = url_for("packages_page", type=type_name, q=search, page=query.prev_num) \
			if query.has_prev else None

	topics = None
	if qb.search and not query.has_next:
		topics = qb.buildTopicQuery().all()

	tags = Tag.query.all()
	return render_template("packages/list.html", \
			title=title, packages=query.items, topics=topics, \
			query=search, tags=tags, type=type_name, \
			next_url=next_url, prev_url=prev_url, page=page, page_max=query.pages, packages_count=query.total)


def getReleases(package):
	if package.checkPerm(current_user, Permission.MAKE_RELEASE):
		return package.releases
	else:
		return [rel for rel in package.releases if rel.approved]


@app.route("/packages/<author>/<name>/")
@is_package_page
def package_page(package):
	clearNotifications(package.getDetailsURL())

	alternatives = None
	if package.type == PackageType.MOD:
		alternatives = Package.query \
			.filter_by(name=package.name, type=PackageType.MOD, soft_deleted=False) \
			.filter(Package.id != package.id) \
			.order_by(db.desc(Package.score)) \
			.all()


	show_similar_topics = current_user == package.author or \
			package.checkPerm(current_user, Permission.APPROVE_NEW)

	similar_topics = None if not show_similar_topics else \
			ForumTopic.query \
				.filter_by(name=package.name) \
				.filter(ForumTopic.topic_id != package.forums) \
				.filter(~ db.exists().where(Package.forums==ForumTopic.topic_id)) \
				.order_by(db.asc(ForumTopic.name), db.asc(ForumTopic.title)) \
				.all()

	releases = getReleases(package)
	requests = [r for r in package.requests if r.status == 0]

	review_thread = package.review_thread
	if review_thread is not None and not review_thread.checkPerm(current_user, Permission.SEE_THREAD):
		review_thread = None

	topic_error = None
	topic_error_lvl = "warning"
	if not package.approved and package.forums is not None:
		errors = []
		if Package.query.filter_by(forums=package.forums, soft_deleted=False).count() > 1:
			errors.append("<b>Error: Another package already uses this forum topic!</b>")
			topic_error_lvl = "danger"

		topic = ForumTopic.query.get(package.forums)
		if topic is not None:
			if topic.author != package.author:
				errors.append("<b>Error: Forum topic author doesn't match package author.</b>")
				topic_error_lvl = "danger"

			if topic.wip:
				errors.append("Warning: Forum topic is in WIP section, make sure package meets playability standards.")
		elif package.type != PackageType.TXP:
			errors.append("Warning: Forum topic not found. This may happen if the topic has only just been created.")

		topic_error = "<br />".join(errors)


	threads = Thread.query.filter_by(package_id=package.id)
	if not current_user.is_authenticated:
		threads = threads.filter_by(private=False)
	elif not current_user.rank.atLeast(UserRank.EDITOR) and not current_user == package.author:
		threads = threads.filter(or_(Thread.private == False, Thread.author == current_user))


	return render_template("packages/view.html", \
			package=package, releases=releases, requests=requests, \
			alternatives=alternatives, similar_topics=similar_topics, \
			review_thread=review_thread, topic_error=topic_error, topic_error_lvl=topic_error_lvl, \
			threads=threads.all())


@app.route("/packages/<author>/<name>/download/")
@is_package_page
def package_download_page(package):
	release = package.getDownloadRelease()

	if release is None:
		if "application/zip" in request.accept_mimetypes and \
				not "text/html" in request.accept_mimetypes:
			return "", 204
		else:
			flash("No download available.", "error")
			return redirect(package.getDetailsURL())
	else:
		return redirect(release.url, code=302)


class PackageForm(FlaskForm):
	name          = StringField("Name (Technical)", [InputRequired(), Length(1, 20), Regexp("^[a-z0-9_]", 0, "Lower case letters (a-z), digits (0-9), and underscores (_) only")])
	title         = StringField("Title (Human-readable)", [InputRequired(), Length(3, 50)])
	shortDesc     = StringField("Short Description (Plaintext)", [InputRequired(), Length(1,200)])
	desc          = TextAreaField("Long Description (Markdown)", [Optional(), Length(0,10000)])
	type          = SelectField("Type", [InputRequired()], choices=PackageType.choices(), coerce=PackageType.coerce, default=PackageType.MOD)
	license       = QuerySelectField("License", [InputRequired()], query_factory=lambda: License.query.order_by(db.asc(License.name)), get_pk=lambda a: a.id, get_label=lambda a: a.name)
	media_license = QuerySelectField("Media License", [InputRequired()], query_factory=lambda: License.query.order_by(db.asc(License.name)), get_pk=lambda a: a.id, get_label=lambda a: a.name)
	provides_str  = StringField("Provides (mods included in package)", [Optional(), Length(0,1000)])
	tags          = QuerySelectMultipleField('Tags', query_factory=lambda: Tag.query.order_by(db.asc(Tag.name)), get_pk=lambda a: a.id, get_label=lambda a: a.title)
	harddep_str   = StringField("Hard Dependencies", [Optional(), Length(0,1000)])
	softdep_str   = StringField("Soft Dependencies", [Optional(), Length(0,1000)])
	repo          = StringField("VCS Repository URL", [Optional(), URL()])
	website       = StringField("Website URL", [Optional(), URL()])
	issueTracker  = StringField("Issue Tracker URL", [Optional(), URL()])
	forums	      = IntegerField("Forum Topic ID", [Optional(), NumberRange(0,999999)])
	submit	      = SubmitField("Save")

@app.route("/packages/new/", methods=["GET", "POST"])
@app.route("/packages/<author>/<name>/edit/", methods=["GET", "POST"])
@login_required
def create_edit_package_page(author=None, name=None):
	package = None
	form = None
	if author is None:
		form = PackageForm(formdata=request.form)
		author = request.args.get("author")
		if author is None or author == current_user.username:
			author = current_user
		else:
			author = User.query.filter_by(username=author).first()
			if author is None:
				flash("Unable to find that user", "error")
				return redirect(url_for("create_edit_package_page"))

			if not author.checkPerm(current_user, Permission.CHANGE_AUTHOR):
				flash("Permission denied", "error")
				return redirect(url_for("create_edit_package_page"))

	else:
		package = getPackageByInfo(author, name)
		if not package.checkPerm(current_user, Permission.EDIT_PACKAGE):
			return redirect(package.getDetailsURL())

		author = package.author

		form = PackageForm(formdata=request.form, obj=package)

	# Initial form class from post data and default data
	if request.method == "GET":
		if package is None:
			form.name.data   = request.args.get("bname")
			form.title.data  = request.args.get("title")
			form.repo.data   = request.args.get("repo")
			form.forums.data = request.args.get("forums")
		else:
			deps = package.dependencies
			form.harddep_str.data  = ",".join([str(x) for x in deps if not x.optional])
			form.softdep_str.data  = ",".join([str(x) for x in deps if     x.optional])
			form.provides_str.data = MetaPackage.ListToSpec(package.provides)

	if request.method == "POST" and form.validate():
		wasNew = False
		if not package:
			package = Package.query.filter_by(name=form["name"].data, author_id=author.id).first()
			if package is not None:
				if package.soft_deleted:
					Package.query.filter_by(name=form["name"].data, author_id=author.id).delete()
				else:
					flash("Package already exists!", "error")
					return redirect(url_for("create_edit_package_page"))

			package = Package()
			package.author = author
			wasNew = True
		else:
			triggerNotif(package.author, current_user,
					"{} edited".format(package.title), package.getDetailsURL())

		form.populate_obj(package) # copy to row

		mpackage_cache = {}
		package.provides.clear()
		mpackages = MetaPackage.SpecToList(form.provides_str.data, mpackage_cache)
		for m in mpackages:
			package.provides.append(m)

		Dependency.query.filter_by(depender=package).delete()
		deps = Dependency.SpecToList(package, form.harddep_str.data, mpackage_cache)
		for dep in deps:
			dep.optional = False
			db.session.add(dep)

		deps = Dependency.SpecToList(package, form.softdep_str.data, mpackage_cache)
		for dep in deps:
			dep.optional = True
			db.session.add(dep)

		if wasNew and package.type == PackageType.MOD and not package.name in mpackage_cache:
			m = MetaPackage.GetOrCreate(package.name, mpackage_cache)
			package.provides.append(m)

		package.tags.clear()
		for tag in form.tags.raw_data:
			package.tags.append(Tag.query.get(tag))

		db.session.commit() # save

		next_url = package.getDetailsURL()
		if wasNew and package.repo is not None:
			task = importRepoScreenshot.delay(package.id)
			next_url = url_for("check_task", id=task.id, r=next_url)

		if wasNew and ("WTFPL" in package.license.name or "WTFPL" in package.media_license.name):
			next_url = url_for("flatpage", path="help/wtfpl", r=next_url)

		return redirect(next_url)

	package_query = Package.query.filter_by(approved=True, soft_deleted=False)
	if package is not None:
		package_query = package_query.filter(Package.id != package.id)

	enableWizard = name is None and request.method != "POST"
	return render_template("packages/create_edit.html", package=package, \
			form=form, author=author, enable_wizard=enableWizard, \
			packages=package_query.all(), \
			mpackages=MetaPackage.query.order_by(db.asc(MetaPackage.name)).all())

@app.route("/packages/<author>/<name>/approve/", methods=["POST"])
@login_required
@is_package_page
def approve_package_page(package):
	if not package.checkPerm(current_user, Permission.APPROVE_NEW):
		flash("You don't have permission to do that.", "error")

	elif package.approved:
		flash("Package has already been approved", "error")

	else:
		package.approved = True

		screenshots = PackageScreenshot.query.filter_by(package=package, approved=False).all()
		for s in screenshots:
			s.approved = True

		triggerNotif(package.author, current_user,
				"{} approved".format(package.title), package.getDetailsURL())
		db.session.commit()

	return redirect(package.getDetailsURL())


@app.route("/packages/<author>/<name>/delete/", methods=["GET", "POST"])
@login_required
@is_package_page
def delete_package_page(package):
	if request.method == "GET":
		return render_template("packages/delete.html", package=package)

	if not package.checkPerm(current_user, Permission.DELETE_PACKAGE):
		flash("You don't have permission to do that.", "error")

	package.soft_deleted = True

	url = url_for("user_profile_page", username=package.author.username)
	triggerNotif(package.author, current_user,
			"{} deleted".format(package.title), url)
	db.session.commit()

	flash("Deleted package", "success")

	return redirect(url)

from . import todo, screenshots, releases
