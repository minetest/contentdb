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


from functools import wraps

from flask_login import login_user, current_user
from passlib.handlers.bcrypt import bcrypt
from flask import redirect, url_for, abort

from app.models import User, UserRank, UserNotificationPreferences, db


def check_password_hash(stored, given):
	if stored is None or stored == "":
		return False

	return bcrypt.verify(given.encode("UTF-8"), stored)


def make_flask_login_password(plaintext):
	return bcrypt.hash(plaintext.encode("UTF-8"))


def login_user_set_active(user: User, *args, **kwargs):
	if user.rank == UserRank.NOT_JOINED and user.email is None:
		user.rank = UserRank.MEMBER
		user.notification_preferences = UserNotificationPreferences(user)
		user.is_active = True
		db.session.commit()

	return login_user(user, *args, **kwargs)


def rank_required(rank):
	def decorator(f):
		@wraps(f)
		def decorated_function(*args, **kwargs):
			if not current_user.is_authenticated:
				return redirect(url_for("users.login"))
			if not current_user.rank.atLeast(rank):
				abort(403)

			return f(*args, **kwargs)

		return decorated_function
	return decorator
