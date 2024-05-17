# ContentDB
# Copyright (C) 2024 rubenwardy
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

import datetime
from flask import render_template, request, abort, redirect, url_for, jsonify

from . import bp
from app.logic.approval_stats import get_approval_statistics
from app.models import UserRank
from app.utils import rank_required


@bp.route("/admin/approval_stats/")
@rank_required(UserRank.APPROVER)
def approval_stats():
	start = request.args.get("start")
	end = request.args.get("end")
	if start and end:
		try:
			start = datetime.datetime.fromisoformat(start)
			end = datetime.datetime.fromisoformat(end)
		except ValueError:
			abort(400)
	elif start:
		return redirect(url_for("admin.approval_stats", start=start, end=datetime.datetime.utcnow().date().isoformat()))
	elif end:
		return redirect(url_for("admin.approval_stats", start="2020-07-01", end=end))
	else:
		end = datetime.datetime.utcnow()
		start = end - datetime.timedelta(days=365)

	stats = get_approval_statistics(start, end)
	return render_template("admin/approval_stats.html", stats=stats, start=start, end=end)


@bp.route("/admin/approval_stats.json")
@rank_required(UserRank.APPROVER)
def approval_stats_json():
	start = request.args.get("start")
	end = request.args.get("end")
	if start and end:
		try:
			start = datetime.datetime.fromisoformat(start)
			end = datetime.datetime.fromisoformat(end)
		except ValueError:
			abort(400)
	else:
		end = datetime.datetime.utcnow()
		start = end - datetime.timedelta(days=365)

	stats = get_approval_statistics(start, end)
	for key, value in stats.packages_info.items():
		stats.packages_info[key] = value.__dict__()

	return jsonify({
		"start": start.isoformat(),
		"end": end.isoformat(),
		"editor_approvals": stats.editor_approvals,
		"packages_info": stats.packages_info,
		"turnaround_time": {
			"avg": stats.avg_turnaround_time,
			"max": stats.max_turnaround_time,
		},
	})
