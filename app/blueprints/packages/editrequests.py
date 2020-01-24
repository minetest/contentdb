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
from app import app
from app.models import *

from app.utils import *

from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField

from . import PackageForm


class EditRequestForm(PackageForm):
	edit_title = StringField("Edit Title", [InputRequired(), Length(1, 100)])
	edit_desc  = TextField("Edit Description", [Optional()])

@app.route("/packages/<author>/<name>/requests/new/", methods=["GET","POST"])
@app.route("/packages/<author>/<name>/requests/<id>/edit/", methods=["GET","POST"])
@login_required
@is_package_page
def create_edit_editrequest_page(package, id=None):
	edited_package = package

	erequest = None
	if id is not None:
		erequest = EditRequest.query.get(id)
		if erequest.package != package:
			abort(404)

		if not erequest.checkPerm(current_user, Permission.EDIT_EDITREQUEST):
			abort(403)

		if erequest.status != 0:
			flash("Can't edit EditRequest, it has already been merged or rejected", "danger")
			return redirect(erequest.getURL())

		edited_package = Package(package)
		erequest.applyAll(edited_package)

	form = EditRequestForm(request.form, obj=edited_package)
	if request.method == "GET":
		deps = edited_package.dependencies
		form.harddep_str.data  = ",".join([str(x) for x in deps if not x.optional])
		form.softdep_str.data  = ",".join([str(x) for x in deps if     x.optional])
		form.provides_str.data = MetaPackage.ListToSpec(edited_package.provides)

	if request.method == "POST" and form.validate():
		if erequest is None:
			erequest = EditRequest()
			erequest.package = package
			erequest.author  = current_user

		erequest.title   = form["edit_title"].data
		erequest.desc    = form["edit_desc"].data
		db.session.add(erequest)

		EditRequestChange.query.filter_by(request=erequest).delete()

		wasChangeMade = False
		for e in PackagePropertyKey:
			newValue = form[e.name].data
			oldValue = getattr(package, e.name)

			newValueComp = newValue
			oldValueComp = oldValue
			if type(newValue) is str:
				newValue = newValue.replace("\r\n", "\n")
				newValueComp = newValue.strip()
				oldValueComp = "" if oldValue is None else oldValue.strip()

			if newValueComp != oldValueComp:
				change = EditRequestChange()
				change.request = erequest
				change.key = e
				change.oldValue = e.convert(oldValue)
				change.newValue = e.convert(newValue)
				db.session.add(change)
				wasChangeMade = True

		if wasChangeMade:
			msg = "{}: Edit request #{} {}" \
					.format(package.title, erequest.id, "created" if id is None else "edited")
			triggerNotif(package.author, current_user, msg, erequest.getURL())
			triggerNotif(erequest.author, current_user, msg, erequest.getURL())
			db.session.commit()
			return redirect(erequest.getURL())
		else:
			flash("No changes detected", "warning")
	elif erequest is not None:
		form["edit_title"].data = erequest.title
		form["edit_desc"].data  = erequest.desc

	return render_template("packages/editrequest_create_edit.html", package=package, form=form)


@app.route("/packages/<author>/<name>/requests/<id>/")
@is_package_page
def view_editrequest_page(package, id):
	erequest = EditRequest.query.get(id)
	if erequest is None or erequest.package != package:
		abort(404)

	clearNotifications(erequest.getURL())
	return render_template("packages/editrequest_view.html", package=package, request=erequest)


@app.route("/packages/<author>/<name>/requests/<id>/approve/", methods=["POST"])
@is_package_page
def approve_editrequest_page(package, id):
	if not package.checkPerm(current_user, Permission.APPROVE_CHANGES):
		flash("You don't have permission to do that.", "danger")
		return redirect(package.getDetailsURL())

	erequest = EditRequest.query.get(id)
	if erequest is None or erequest.package != package:
		abort(404)

	if erequest.status != 0:
		flash("Edit request has already been resolved", "danger")

	else:
		erequest.status = 1
		erequest.applyAll(package)

		msg = "{}: Edit request #{} merged".format(package.title, erequest.id)
		triggerNotif(erequest.author, current_user, msg, erequest.getURL())
		triggerNotif(package.author, current_user, msg, erequest.getURL())
		db.session.commit()

	return redirect(package.getDetailsURL())

@app.route("/packages/<author>/<name>/requests/<id>/reject/", methods=["POST"])
@is_package_page
def reject_editrequest_page(package, id):
	if not package.checkPerm(current_user, Permission.APPROVE_CHANGES):
		flash("You don't have permission to do that.", "danger")
		return redirect(package.getDetailsURL())

	erequest = EditRequest.query.get(id)
	if erequest is None or erequest.package != package:
		abort(404)

	if erequest.status != 0:
		flash("Edit request has already been resolved", "danger")

	else:
		erequest.status = 2

		msg = "{}: Edit request #{} rejected".format(package.title, erequest.id)
		triggerNotif(erequest.author, current_user, msg, erequest.getURL())
		triggerNotif(package.author, current_user, msg, erequest.getURL())
		db.session.commit()

	return redirect(package.getDetailsURL())
