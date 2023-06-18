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
from flask_babel import gettext, lazy_gettext
from flask_wtf import FlaskForm
from flask_login import login_required
from wtforms import *
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import *

from app.utils import *
from . import bp, get_package_tabs
from app.logic.LogicError import LogicError
from app.logic.screenshots import do_create_screenshot, do_order_screenshots


class CreateScreenshotForm(FlaskForm):
	title	   = StringField(lazy_gettext("Title/Caption"), [Optional(), Length(-1, 100)])
	file_upload = FileField(lazy_gettext("File Upload"), [InputRequired()])
	submit	   = SubmitField(lazy_gettext("Save"))


class EditScreenshotForm(FlaskForm):
	title	 = StringField(lazy_gettext("Title/Caption"), [Optional(), Length(-1, 100)])
	approved = BooleanField(lazy_gettext("Is Approved"))
	submit   = SubmitField(lazy_gettext("Save"))


class EditPackageScreenshotsForm(FlaskForm):
	cover_image      = QuerySelectField(lazy_gettext("Cover Image"), [DataRequired()], allow_blank=True, get_pk=lambda a: a.id, get_label=lambda a: a.title)
	submit	         = SubmitField(lazy_gettext("Save"))


@bp.route("/packages/<author>/<name>/screenshots/", methods=["GET", "POST"])
@login_required
@is_package_page
def screenshots(package):
	if not package.check_perm(current_user, Permission.ADD_SCREENSHOTS):
		return redirect(package.get_url("packages.view"))

	form = EditPackageScreenshotsForm(obj=package)
	form.cover_image.query = package.screenshots

	if request.method == "POST":
		order = request.form.get("order")
		if order:
			try:
				do_order_screenshots(current_user, package, order.split(","))
				return redirect(package.get_url("packages.view"))
			except LogicError as e:
				flash(e.message, "danger")

		if form.validate_on_submit():
			form.populate_obj(package)
			db.session.commit()

	return render_template("packages/screenshots.html", package=package, form=form,
			tabs=get_package_tabs(current_user, package), current_tab="screenshots")


@bp.route("/packages/<author>/<name>/screenshots/new/", methods=["GET", "POST"])
@login_required
@is_package_page
def create_screenshot(package):
	if not package.check_perm(current_user, Permission.ADD_SCREENSHOTS):
		return redirect(package.get_url("packages.view"))

	# Initial form class from post data and default data
	form = CreateScreenshotForm()
	if form.validate_on_submit():
		try:
			do_create_screenshot(current_user, package, form.title.data, form.file_upload.data, False)
			return redirect(package.get_url("packages.screenshots"))
		except LogicError as e:
			flash(e.message, "danger")

	return render_template("packages/screenshot_new.html", package=package, form=form)


@bp.route("/packages/<author>/<name>/screenshots/<id>/edit/", methods=["GET", "POST"])
@login_required
@is_package_page
def edit_screenshot(package, id):
	screenshot = PackageScreenshot.query.get(id)
	if screenshot is None or screenshot.package != package:
		abort(404)

	canEdit	= package.check_perm(current_user, Permission.ADD_SCREENSHOTS)
	canApprove = package.check_perm(current_user, Permission.APPROVE_SCREENSHOT)
	if not (canEdit or canApprove):
		return redirect(package.get_url("packages.screenshots"))

	# Initial form class from post data and default data
	form = EditScreenshotForm(obj=screenshot)
	if form.validate_on_submit():
		wasApproved = screenshot.approved

		if canEdit:
			screenshot.title = form["title"].data or "Untitled"

		if canApprove:
			screenshot.approved = form["approved"].data
		else:
			screenshot.approved = wasApproved

		db.session.commit()
		return redirect(package.get_url("packages.screenshots"))

	return render_template("packages/screenshot_edit.html", package=package, screenshot=screenshot, form=form)


@bp.route("/packages/<author>/<name>/screenshots/<id>/delete/", methods=["POST"])
@login_required
@is_package_page
def delete_screenshot(package, id):
	screenshot = PackageScreenshot.query.get(id)
	if screenshot is None or screenshot.package != package:
		abort(404)

	if not package.check_perm(current_user, Permission.ADD_SCREENSHOTS):
		flash(gettext("Permission denied"), "danger")
		return redirect(url_for("homepage.home"))

	if package.cover_image == screenshot:
		package.cover_image = None
		db.session.merge(package)

	db.session.delete(screenshot)
	db.session.commit()

	return redirect(package.get_url("packages.screenshots"))
