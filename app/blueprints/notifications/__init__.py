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


from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField
from app.blueprints.users.profile import get_setting_tabs
from app.models import db, Notification, UserNotificationPreferences, NotificationType

bp = Blueprint("notifications", __name__)


@bp.route("/notifications/")
@login_required
def list_all():
	return render_template("notifications/list.html")


@bp.route("/notifications/clear/", methods=["POST"])
@login_required
def clear():
	Notification.query.filter_by(user=current_user).delete()
	db.session.commit()
	return redirect(url_for("notifications.list_all"))


@bp.route("/notifications/settings/", methods=["GET", "POST"])
@login_required
def settings():
	is_new = False
	prefs = current_user.notification_preferences
	if prefs is None:
		is_new = True
		prefs = UserNotificationPreferences(current_user)

	attrs = {
		"submit": SubmitField("Save")
	}

	data = {}
	types = []
	for notificationType in NotificationType:
		key = "pref_" + notificationType.toName()
		types.append(notificationType)
		attrs[key] = BooleanField("")
		data[key] = getattr(prefs, key) == 2

	SettingsForm = type("SettingsForm", (FlaskForm,), attrs)

	form = SettingsForm(data=data)
	if form.validate_on_submit():
		for notificationType in NotificationType:
			key = "pref_" + notificationType.toName()
			field = getattr(form, key)
			value = 2 if field.data else 0
			setattr(prefs, key, value)

		if is_new:
			db.session.add(prefs)

		db.session.commit()
		return redirect(url_for("notifications.settings"))

	return render_template("notifications/settings.html",
			form=form, user=current_user, types=types, is_new=is_new,
			tabs=get_setting_tabs(current_user), current_tab="notifications")
