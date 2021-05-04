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


from flask import *
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import *

from app.logic.releases import do_create_vcs_release, LogicError, do_create_zip_release
from app.rediscache import has_key, set_key, make_download_key
from app.tasks.importtasks import check_update_config
from app.utils import *
from . import bp, get_package_tabs


@bp.route("/packages/<author>/<name>/releases/", methods=["GET", "POST"])
@is_package_page
def list_releases(package):
	return render_template("packages/releases_list.html",
			package=package,
			tabs=get_package_tabs(current_user, package), current_tab="releases")


def get_mt_releases(is_max):
	query = MinetestRelease.query.order_by(db.asc(MinetestRelease.id))
	if is_max:
		query = query.limit(query.count() - 1)
	else:
		query = query.filter(MinetestRelease.name != "0.4.17")

	return query


class CreatePackageReleaseForm(FlaskForm):
	title	   = StringField("Title", [InputRequired(), Length(1, 30)])
	uploadOpt  = RadioField ("Method", choices=[("upload", "File Upload")], default="upload")
	vcsLabel   = StringField("Git reference (ie: commit hash, branch, or tag)", default=None)
	fileUpload = FileField("File Upload")
	min_rel    = QuerySelectField("Minimum Minetest Version", [InputRequired()],
			query_factory=lambda: get_mt_releases(False), get_pk=lambda a: a.id, get_label=lambda a: a.name)
	max_rel    = QuerySelectField("Maximum Minetest Version", [InputRequired()],
			query_factory=lambda: get_mt_releases(True), get_pk=lambda a: a.id, get_label=lambda a: a.name)
	submit	   = SubmitField("Save")

class EditPackageReleaseForm(FlaskForm):
	title    = StringField("Title", [InputRequired(), Length(1, 30)])
	url      = StringField("URL", [Optional()])
	task_id  = StringField("Task ID", filters = [lambda x: x or None])
	approved = BooleanField("Is Approved")
	min_rel  = QuerySelectField("Minimum Minetest Version", [InputRequired()],
			query_factory=lambda: get_mt_releases(False), get_pk=lambda a: a.id, get_label=lambda a: a.name)
	max_rel  = QuerySelectField("Maximum Minetest Version", [InputRequired()],
			query_factory=lambda: get_mt_releases(True), get_pk=lambda a: a.id, get_label=lambda a: a.name)
	submit   = SubmitField("Save")


@bp.route("/packages/<author>/<name>/releases/new/", methods=["GET", "POST"])
@login_required
@is_package_page
def create_release(package):
	if not package.checkPerm(current_user, Permission.MAKE_RELEASE):
		return redirect(package.getDetailsURL())

	# Initial form class from post data and default data
	form = CreatePackageReleaseForm()
	if package.repo is not None:
		form["uploadOpt"].choices = [("vcs", "Import from Git"), ("upload", "Upload .zip file")]
		if request.method == "GET":
			form["uploadOpt"].data = "vcs"
			form.vcsLabel.data = request.args.get("ref")

	if request.method == "GET":
		form.title.data = request.args.get("title")

	if form.validate_on_submit():
		try:
			if form["uploadOpt"].data == "vcs":
				rel = do_create_vcs_release(current_user, package, form.title.data,
						form.vcsLabel.data, form.min_rel.data.getActual(), form.max_rel.data.getActual())
			else:
				rel = do_create_zip_release(current_user, package, form.title.data,
						form.fileUpload.data, form.min_rel.data.getActual(), form.max_rel.data.getActual())
			return redirect(url_for("tasks.check", id=rel.task_id, r=rel.getEditURL()))
		except LogicError as e:
			flash(e.message, "danger")

	return render_template("packages/release_new.html", package=package, form=form)


@bp.route("/packages/<author>/<name>/releases/<id>/download/")
@is_package_page
def download_release(package, id):
	release = PackageRelease.query.get(id)
	if release is None or release.package != package:
		abort(404)

	ip = request.headers.get("X-Forwarded-For") or request.remote_addr
	if ip is not None and not is_user_bot():
		key = make_download_key(ip, release.package)
		if not has_key(key):
			set_key(key, "true")

			bonus = 1

			PackageRelease.query.filter_by(id=release.id).update({
					"downloads": PackageRelease.downloads + 1
				})

			Package.query.filter_by(id=package.id).update({
					"downloads": Package.downloads + 1,
					"score_downloads": Package.score_downloads + bonus,
					"score": Package.score + bonus
				})

			db.session.commit()

	return redirect(release.url)


@bp.route("/packages/<author>/<name>/releases/<id>/", methods=["GET", "POST"])
@login_required
@is_package_page
def edit_release(package, id):
	release : PackageRelease = PackageRelease.query.get(id)
	if release is None or release.package != package:
		abort(404)

	canEdit	= package.checkPerm(current_user, Permission.MAKE_RELEASE)
	canApprove = release.checkPerm(current_user, Permission.APPROVE_RELEASE)
	if not (canEdit or canApprove):
		return redirect(package.getDetailsURL())

	# Initial form class from post data and default data
	form = EditPackageReleaseForm(formdata=request.form, obj=release)

	if request.method == "GET":
		# HACK: fix bug in wtforms
		form.approved.data = release.approved

	if form.validate_on_submit():
		if canEdit:
			release.title = form["title"].data
			release.min_rel = form["min_rel"].data.getActual()
			release.max_rel = form["max_rel"].data.getActual()

		if package.checkPerm(current_user, Permission.CHANGE_RELEASE_URL):
			release.url = form["url"].data
			release.task_id = form["task_id"].data
			if release.task_id is not None:
				release.task_id = None

		if form.approved.data:
			release.approve(current_user)
		elif canApprove:
			release.approved = False

		db.session.commit()
		return redirect(package.getReleaseListURL())

	return render_template("packages/release_edit.html", package=package, release=release, form=form)



class BulkReleaseForm(FlaskForm):
	set_min = BooleanField("Set Min")
	min_rel  = QuerySelectField("Minimum Minetest Version", [InputRequired()],
			query_factory=lambda: get_mt_releases(False), get_pk=lambda a: a.id, get_label=lambda a: a.name)
	set_max = BooleanField("Set Max")
	max_rel  = QuerySelectField("Maximum Minetest Version", [InputRequired()],
			query_factory=lambda: get_mt_releases(True), get_pk=lambda a: a.id, get_label=lambda a: a.name)
	only_change_none = BooleanField("Only change values previously set as none")
	submit   = SubmitField("Update")


@bp.route("/packages/<author>/<name>/releases/bulk_change/", methods=["GET", "POST"])
@login_required
@is_package_page
def bulk_change_release(package):
	if not package.checkPerm(current_user, Permission.MAKE_RELEASE):
		return redirect(package.getDetailsURL())

	# Initial form class from post data and default data
	form = BulkReleaseForm()

	if request.method == "GET":
		form.only_change_none.data = True
	elif form.validate_on_submit():
		only_change_none = form.only_change_none.data

		for release in package.releases.all():
			if form["set_min"].data and (not only_change_none or release.min_rel is None):
				release.min_rel = form["min_rel"].data.getActual()
			if form["set_max"].data and (not only_change_none or release.max_rel is None):
				release.max_rel = form["max_rel"].data.getActual()

		db.session.commit()

		return redirect(package.getReleaseListURL())

	return render_template("packages/release_bulk_change.html", package=package, form=form)


@bp.route("/packages/<author>/<name>/releases/<id>/delete/", methods=["POST"])
@login_required
@is_package_page
def delete_release(package, id):
	release = PackageRelease.query.get(id)
	if release is None or release.package != package:
		abort(404)

	if not release.checkPerm(current_user, Permission.DELETE_RELEASE):
		return redirect(release.getReleaseListURL())

	db.session.delete(release)
	db.session.commit()

	return redirect(package.getDetailsURL())


class PackageUpdateConfigFrom(FlaskForm):
	trigger = RadioField("Trigger", [InputRequired()], choices=PackageUpdateTrigger.choices(), coerce=PackageUpdateTrigger.coerce,
			default=PackageUpdateTrigger.TAG)
	ref     = StringField("Branch name", [Optional()], default=None)
	action  = RadioField("Action", [InputRequired()], choices=[("notification", "Send notification and mark as outdated"), ("make_release", "Create release")], default="make_release")
	submit  = SubmitField("Save Settings")
	disable = SubmitField("Disable Automation")


def set_update_config(package, form):
	if package.update_config is None:
		package.update_config = PackageUpdateConfig()
		db.session.add(package.update_config)

	form.populate_obj(package.update_config)
	package.update_config.ref = nonEmptyOrNone(form.ref.data)
	package.update_config.make_release = form.action.data == "make_release"

	if package.update_config.trigger == PackageUpdateTrigger.COMMIT:
		if package.update_config.last_commit is None:
			last_release = package.releases.first()
			if last_release and last_release.commit_hash:
				package.update_config.last_commit = last_release.commit_hash
	elif package.update_config.trigger == PackageUpdateTrigger.TAG:
		# Only create releases for tags created after this
		package.update_config.last_commit = None
		package.update_config.last_tag = None

	package.update_config.outdated_at = None
	package.update_config.auto_created = False

	db.session.commit()

	if package.update_config.last_commit is None:
		check_update_config.delay(package.id)


@bp.route("/packages/<author>/<name>/update-config/", methods=["GET", "POST"])
@login_required
@is_package_page
def update_config(package):
	if not package.checkPerm(current_user, Permission.MAKE_RELEASE):
		abort(403)

	if not package.repo:
		flash("Please add a Git repository URL in order to set up automatic releases", "danger")
		return redirect(package.getEditURL())

	form = PackageUpdateConfigFrom(obj=package.update_config)
	if request.method == "GET":
		if package.update_config:
			form.action.data = "make_release" if package.update_config.make_release else "notification"
		elif request.args.get("action") == "notification":
			form.trigger.data = PackageUpdateTrigger.COMMIT
			form.action.data = "notification"

		if "trigger" in request.args:
			form.trigger.data = PackageUpdateTrigger.get(request.args["trigger"])

	if form.validate_on_submit():
		if form.disable.data:
			flash("Deleted update configuration", "success")
			if package.update_config:
				db.session.delete(package.update_config)
			db.session.commit()
		else:
			set_update_config(package, form)

		if not form.disable.data and package.releases.count() == 0:
			flash("Now, please create an initial release", "success")
			return redirect(package.getCreateReleaseURL())

		return redirect(package.getReleaseListURL())

	return render_template("packages/update_config.html", package=package, form=form)


@bp.route("/packages/<author>/<name>/setup-releases/")
@login_required
@is_package_page
def setup_releases(package):
	if not package.checkPerm(current_user, Permission.MAKE_RELEASE):
		abort(403)

	if package.update_config:
		return redirect(package.getUpdateConfigURL())

	return render_template("packages/release_wizard.html", package=package)


@bp.route("/user/update-configs/")
@bp.route("/users/<username>/update-configs/", methods=["GET", "POST"])
@login_required
def bulk_update_config(username=None):
	if username is None:
		return redirect(url_for("packages.bulk_update_config", username=current_user.username))

	user: User = User.query.filter_by(username=username).first()
	if not user:
		abort(404)

	if current_user != user and not current_user.rank.atLeast(UserRank.EDITOR):
		abort(403)

	form = PackageUpdateConfigFrom()
	if form.validate_on_submit():
		for package in user.packages.filter(Package.state != PackageState.DELETED, Package.repo.isnot(None)).all():
			set_update_config(package, form)

		return redirect(url_for("packages.bulk_update_config", username=username))

	confs = user.packages \
		.filter(Package.state != PackageState.DELETED,
			Package.update_config.has()) \
		.order_by(db.asc(Package.title)).all()

	return render_template("packages/bulk_update_conf.html", user=user, confs=confs, form=form)
