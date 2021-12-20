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
from flask_login import current_user, login_user
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import InputRequired, Length
from app.utils import rank_required, addAuditLog, addNotification, get_system_user
from . import bp
from .actions import actions
from ...models import UserRank, Package, db, PackageState, User, AuditSeverity, NotificationType


@bp.route("/admin/", methods=["GET", "POST"])
@rank_required(UserRank.ADMIN)
def admin_page():
	if request.method == "POST":
		action = request.form["action"]

		if action == "restore":
			package = Package.query.get(request.form["package"])
			if package is None:
				flash("Unknown package", "danger")
			else:
				package.state = PackageState.READY_FOR_REVIEW
				db.session.commit()
				return redirect(url_for("admin.admin_page"))

		elif action in actions:
			ret = actions[action]["func"]()
			if ret:
				return ret

		else:
			flash("Unknown action: " + action, "danger")

	deleted_packages = Package.query.filter(Package.state==PackageState.DELETED).all()
	return render_template("admin/list.html", deleted_packages=deleted_packages, actions=actions)

class SwitchUserForm(FlaskForm):
	username = StringField("Username")
	submit = SubmitField("Switch")


@bp.route("/admin/switchuser/", methods=["GET", "POST"])
@rank_required(UserRank.ADMIN)
def switch_user():
	form = SwitchUserForm(formdata=request.form)
	if form.validate_on_submit():
		user = User.query.filter_by(username=form["username"].data).first()
		if user is None:
			flash("Unable to find user", "danger")
		elif login_user(user):
			return redirect(url_for("users.profile", username=current_user.username))
		else:
			flash("Unable to login as user", "danger")


	# Process GET or invalid POST
	return render_template("admin/switch_user.html", form=form)


class SendNotificationForm(FlaskForm):
	title  = StringField("Title", [InputRequired(), Length(1, 300)])
	url    = StringField("URL", [InputRequired(), Length(1, 100)], default="/")
	submit = SubmitField("Send")


@bp.route("/admin/send-notification/", methods=["GET", "POST"])
@rank_required(UserRank.ADMIN)
def send_bulk_notification():
	form = SendNotificationForm(request.form)
	if form.validate_on_submit():
		addAuditLog(AuditSeverity.MODERATION, current_user,
				"Sent bulk notification", None, None, form.title.data)

		users = User.query.filter(User.rank >= UserRank.NEW_MEMBER).all()
		addNotification(users, get_system_user(), NotificationType.OTHER, form.title.data, form.url.data, None)
		db.session.commit()

		return redirect(url_for("admin.admin_page"))

	return render_template("admin/send_bulk_notification.html", form=form)


@bp.route("/admin/restore/", methods=["GET", "POST"])
@rank_required(UserRank.EDITOR)
def restore():
	if request.method == "POST":
		target = request.form["submit"]
		if "Review" in target:
			target = PackageState.READY_FOR_REVIEW
		elif "Changes" in target:
			target = PackageState.CHANGES_NEEDED
		else:
			target = PackageState.WIP

		package = Package.query.get(request.form["package"])
		if package is None:
			flash("Unknown package", "danger")
		else:
			package.state = target

			addAuditLog(AuditSeverity.EDITOR, current_user, f"Restored package to state {target.value}",
					package.getURL("packages.view"), package)

			db.session.commit()
			return redirect(package.getURL("packages.view"))

	deleted_packages = Package.query.filter(Package.state==PackageState.DELETED).join(Package.author).order_by(db.asc(User.username), db.asc(Package.name)).all()
	return render_template("admin/restore.html", deleted_packages=deleted_packages)