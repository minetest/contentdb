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
from flask_wtf import FlaskForm
from flask_login import login_required
from wtforms import *
from wtforms.validators import *

from app.utils import *
from . import bp


class CreateScreenshotForm(FlaskForm):
	title	   = StringField("Title/Caption", [Optional(), Length(-1, 100)])
	fileUpload = FileField("File Upload", [InputRequired()])
	submit	   = SubmitField("Save")


class EditScreenshotForm(FlaskForm):
	title	 = StringField("Title/Caption", [Optional(), Length(-1, 100)])
	approved = BooleanField("Is Approved")
	delete   = BooleanField("Delete")
	submit   = SubmitField("Save")

@bp.route("/packages/<author>/<name>/screenshots/new/", methods=["GET", "POST"])
@login_required
@is_package_page
def create_screenshot(package):
	if not package.checkPerm(current_user, Permission.ADD_SCREENSHOTS):
		return redirect(package.getDetailsURL())

	# Initial form class from post data and default data
	form = CreateScreenshotForm()
	if request.method == "POST" and form.validate():
		uploadedUrl, uploadedPath = doFileUpload(form.fileUpload.data, "image",
				"a PNG or JPG image file")
		if uploadedUrl is not None:
			ss = PackageScreenshot()
			ss.package  = package
			ss.title    = form["title"].data or "Untitled"
			ss.url      = uploadedUrl
			ss.approved = package.checkPerm(current_user, Permission.APPROVE_SCREENSHOT)
			db.session.add(ss)

			msg = "Screenshot added {}" \
					.format(ss.title)
			addNotification(package.maintainers, current_user, msg, package.getDetailsURL(), package)
			db.session.commit()
			return redirect(package.getDetailsURL())

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
		return redirect(package.getDetailsURL())

	# Initial form class from post data and default data
	form = EditScreenshotForm(formdata=request.form, obj=screenshot)

	if request.method == "GET":
		# HACK: fix bug in wtforms
		form.approved.data = screenshot.approved

	if request.method == "POST" and form.validate():
		if canEdit and form["delete"].data:
			PackageScreenshot.query.filter_by(id=id).delete()

		else:
			wasApproved = screenshot.approved

			if canEdit:
				screenshot.title = form["title"].data or "Untitled"

			if canApprove:
				screenshot.approved = form["approved"].data
			else:
				screenshot.approved = wasApproved

		db.session.commit()
		return redirect(package.getDetailsURL())

	return render_template("packages/screenshot_edit.html", package=package, screenshot=screenshot, form=form)
