# ContentDB
# Copyright (C) 2020  rubenwardy
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

from flask import render_template, request, abort
from flask_login import current_user, login_required

from app.models import db, AuditLogEntry, UserRank, User, Permission
from app.utils import rank_required, get_int_or_abort

from . import bp


@bp.route("/admin/audit/")
@rank_required(UserRank.MODERATOR)
def audit():
	page = get_int_or_abort(request.args.get("page"), 1)
	num = min(40, get_int_or_abort(request.args.get("n"), 100))

	query = AuditLogEntry.query.order_by(db.desc(AuditLogEntry.created_at))

	if "username" in request.args:
		user = User.query.filter_by(username=request.args.get("username")).first()
		if not user:
			abort(404)
		query = query.filter_by(causer=user)

	pagination = query.paginate(page=page, per_page=num)
	return render_template("admin/audit.html", log=pagination.items, pagination=pagination)


@bp.route("/admin/audit/<int:id_>/")
@login_required
def audit_view(id_):
	entry: AuditLogEntry = AuditLogEntry.query.get_or_404(id_)
	if not entry.checkPerm(current_user, Permission.VIEW_AUDIT_DESCRIPTION):
		abort(403)

	return render_template("admin/audit_view.html", entry=entry)
