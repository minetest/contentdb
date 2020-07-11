# ContentDB
# Copyright (C) 2020  rubenwardy
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
from flask_user import current_user, login_required
from app.models import db, AuditLogEntry, UserRank
from app.utils import rank_required

from . import bp

@bp.route("/admin/audit/")
@login_required
@rank_required(UserRank.MODERATOR)
def audit():
	log = AuditLogEntry.query.order_by(db.desc(AuditLogEntry.created_at)).all()
	return render_template("admin/audit.html", log=log)
