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

from . import bp

from app.rediscache import has_key, set_key, make_download_key
from app.models import *
from app.tasks.importtasks import makeVCSRelease, checkZipRelease, updateMetaFromRelease
from app.utils import *

from celery import uuid
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from wtforms.ext.sqlalchemy.fields import QuerySelectField


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
	vcsLabel   = StringField("VCS Commit Hash, Branch, or Tag", default="master")
	fileUpload = FileField("File Upload")
	min_rel    = QuerySelectField("Minimum Minetest Version", [InputRequired()],
			query_factory=lambda: get_mt_releases(False), get_pk=lambda a: a.id, get_label=lambda a: a.name)
	max_rel    = QuerySelectField("Maximum Minetest Version", [InputRequired()],
			query_factory=lambda: get_mt_releases(True), get_pk=lambda a: a.id, get_label=lambda a: a.name)
	submit	   = SubmitField("Save")

class EditPackageReleaseForm(FlaskForm):
	title    = StringField("Title", [InputRequired(), Length(1, 30)])
	url      = StringField("URL", [URL])
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
		form["uploadOpt"].choices = [("vcs", "From Git Commit or Branch"), ("upload", "File Upload")]
		if request.method != "POST":
			form["uploadOpt"].data = "vcs"

	if request.method == "POST" and form.validate():
		if form["uploadOpt"].data == "vcs":
			rel = PackageRelease()
			rel.package = package
			rel.title   = form["title"].data
			rel.url     = ""
			rel.task_id = uuid()
			rel.min_rel = form["min_rel"].data.getActual()
			rel.max_rel = form["max_rel"].data.getActual()
			db.session.add(rel)
			db.session.commit()

			makeVCSRelease.apply_async((rel.id, form["vcsLabel"].data), task_id=rel.task_id)

			msg = "Release {} created".format(rel.title)
			addNotification(package.maintainers, current_user, msg, rel.getEditURL(), package)
			db.session.commit()

			return redirect(url_for("tasks.check", id=rel.task_id, r=rel.getEditURL()))
		else:
			uploadedUrl, uploadedPath = doFileUpload(form.fileUpload.data, "zip", "a zip file")
			if uploadedUrl is not None:
				rel = PackageRelease()
				rel.package = package
				rel.title = form["title"].data
				rel.url = uploadedUrl
				rel.task_id = uuid()
				rel.min_rel = form["min_rel"].data.getActual()
				rel.max_rel = form["max_rel"].data.getActual()
				db.session.add(rel)
				db.session.commit()

				checkZipRelease.apply_async((rel.id, uploadedPath), task_id=rel.task_id)
				updateMetaFromRelease.delay(rel.id, uploadedPath)

				msg = "Release {} created".format(rel.title)
				addNotification(package.maintainers, current_user, msg, rel.getEditURL(), package)
				db.session.commit()

				return redirect(url_for("tasks.check", id=rel.task_id, r=rel.getEditURL()))

	return render_template("packages/release_new.html", package=package, form=form)


@bp.route("/packages/<author>/<name>/releases/<id>/download/")
@is_package_page
def download_release(package, id):
	release = PackageRelease.query.get(id)
	if release is None or release.package != package:
		abort(404)

	ip = request.headers.get("X-Forwarded-For") or request.remote_addr
	if ip is not None:
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

	return redirect(release.url, code=300)


@bp.route("/packages/<author>/<name>/releases/<id>/", methods=["GET", "POST"])
@login_required
@is_package_page
def edit_release(package, id):
	release = PackageRelease.query.get(id)
	if release is None or release.package != package:
		abort(404)

	canEdit	= package.checkPerm(current_user, Permission.MAKE_RELEASE)
	canApprove = package.checkPerm(current_user, Permission.APPROVE_RELEASE)
	if not (canEdit or canApprove):
		return redirect(package.getDetailsURL())

	# Initial form class from post data and default data
	form = EditPackageReleaseForm(formdata=request.form, obj=release)

	if request.method == "GET":
		# HACK: fix bug in wtforms
		form.approved.data = release.approved

	if request.method == "POST" and form.validate():
		wasApproved = release.approved
		if canEdit:
			release.title = form["title"].data
			release.min_rel = form["min_rel"].data.getActual()
			release.max_rel = form["max_rel"].data.getActual()

		if package.checkPerm(current_user, Permission.CHANGE_RELEASE_URL):
			release.url = form["url"].data
			release.task_id = form["task_id"].data
			if release.task_id is not None:
				release.task_id = None

		if canApprove:
			release.approved = form["approved"].data
		else:
			release.approved = wasApproved

		db.session.commit()
		return redirect(package.getDetailsURL())

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
	elif request.method == "POST" and form.validate():
		only_change_none = form.only_change_none.data

		for release in package.releases.all():
			if form["set_min"].data and (not only_change_none or release.min_rel is None):
				release.min_rel = form["min_rel"].data.getActual()
			if form["set_max"].data and (not only_change_none or release.max_rel is None):
				release.max_rel = form["max_rel"].data.getActual()

		db.session.commit()

		return redirect(package.getDetailsURL())

	return render_template("packages/release_bulk_change.html", package=package, form=form)


@bp.route("/packages/<author>/<name>/releases/<id>/delete/", methods=["POST"])
@login_required
@is_package_page
def delete_release(package, id):
	release = PackageRelease.query.get(id)
	if release is None or release.package != package:
		abort(404)

	if not release.checkPerm(current_user, Permission.DELETE_RELEASE):
		return redirect(release.getEditURL())

	db.session.delete(release)
	db.session.commit()

	return redirect(package.getDetailsURL())
