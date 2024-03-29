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

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_, desc

from app.models import db, Notification, NotificationType

bp = Blueprint("notifications", __name__)


@bp.route("/notifications/")
@login_required
def list_all():
	notifications = Notification.query.filter(Notification.user == current_user,
			Notification.type != NotificationType.EDITOR_ALERT, Notification.type != NotificationType.EDITOR_MISC) \
			.order_by(desc(Notification.created_at)) \
			.all()

	editor_notifications = Notification.query.filter(Notification.user == current_user,
			or_(Notification.type == NotificationType.EDITOR_ALERT, Notification.type == NotificationType.EDITOR_MISC)) \
			.order_by(desc(Notification.created_at)) \
			.all()

	return render_template("notifications/list.html",
			notifications=notifications, editor_notifications=editor_notifications)


@bp.route("/notifications/clear/", methods=["POST"])
@login_required
def clear():
	Notification.query.filter_by(user=current_user).delete()
	db.session.commit()
	return redirect(url_for("notifications.list_all"))
