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
from flask_wtf import FlaskForm
from flask_login import login_required
from wtforms import *
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import *

from app.utils import *
from . import bp, get_package_tabs
from app.logic.LogicError import LogicError
from app.logic.screenshots import do_create_screenshot, do_order_screenshots


class CreateScreenshotForm(FlaskForm):
	title	   = StringField("Title/Caption", [Optional(), Length(-1, 100)])
	fileUpload = FileField("File Upload", [InputRequired()])
	submit	   = SubmitField("Save")


class EditScreenshotForm(FlaskForm):
	title	 = StringField("Title/Caption", [Optional(), Length(-1, 100)])
	approved = BooleanField("Is Approved")
	submit   = SubmitField("Save")


class EditPackageScreenshotsForm(FlaskForm):
	cover_image      = QuerySelectField("Cover Image", [DataRequired()], allow_blank=True, get_pk=lambda a: a.id, get_label=lambda a: a.title)
	submit	         = SubmitField("Save")


@bp.route("/packages/<author>/<name>/screenshots/", methods=["GET", "POST"])
@login_required
@is_package_page
def screenshots(package):
	if not package.checkPerm(current_user, Permission.ADD_SCREENSHOTS):
		return redirect(package.getDetailsURL())

	if package.screenshots.count() == 0:
		return redirect(package.getNewScreenshotURL())

	form = EditPackageScreenshotsForm(obj=package)
	form.cover_image.query = package.screenshots

	if request.method == "POST":
		order = request.form.get("order")
		if order:
			try:
				do_order_screenshots(current_user, package, order.split(","))
				return redirect(package.getDetailsURL())
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
	if not package.checkPerm(current_user, Permission.ADD_SCREENSHOTS):
		return redirect(package.getDetailsURL())

	# Initial form class from post data and default data
	form = CreateScreenshotForm()
	if form.validate_on_submit():
		try:
			do_create_screenshot(current_user, package, form.title.data, form.fileUpload.data)
			return redirect(package.getEditScreenshotsURL())
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

	canEdit	= package.checkPerm(current_user, Permission.ADD_SCREENSHOTS)
	canApprove = package.checkPerm(current_user, Permission.APPROVE_SCREENSHOT)
	if not (canEdit or canApprove):
		return redirect(package.getEditScreenshotsURL())

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
		return redirect(package.getEditScreenshotsURL())

	return render_template("packages/screenshot_edit.html", package=package, screenshot=screenshot, form=form)


@bp.route("/packages/<author>/<name>/screenshots/<id>/delete/", methods=["POST"])
@login_required
@is_package_page
def delete_screenshot(package, id):
	screenshot = PackageScreenshot.query.get(id)
	if screenshot is None or screenshot.package != package:
		abort(404)

	if not package.checkPerm(current_user, Permission.ADD_SCREENSHOTS):
		flash("Permission denied", "danger")
		return redirect(url_for("homepage.home"))

	if package.cover_image == screenshot:
		package.cover_image = None
		db.session.merge(package)

	db.session.delete(screenshot)
	db.session.commit()

	return redirect(package.getEditScreenshotsURL())
