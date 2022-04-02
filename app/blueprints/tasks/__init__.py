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
from flask_login import login_required

from app import csrf
from app.tasks import celery
from app.tasks.importtasks import getMeta
from app.utils import *

bp = Blueprint("tasks", __name__)


@csrf.exempt
@bp.route("/tasks/getmeta/new/", methods=["POST"])
@login_required
def start_getmeta():
	author = request.args.get("author")
	author = current_user.forums_username if author is None else author
	aresult = getMeta.delay(request.args.get("url"), author)
	return jsonify({
		"poll_url": url_for("tasks.check", id=aresult.id),
	})


@bp.route("/tasks/<id>/")
def check(id):
	result = celery.AsyncResult(id)
	status = result.status
	traceback = result.traceback
	result = result.result

	if isinstance(result, Exception):
		info = {
				'id': id,
				'status': status,
			}

		if current_user.is_authenticated and current_user.rank.atLeast(UserRank.ADMIN):
			info["error"] = str(traceback)
		elif str(result)[1:12] == "TaskError: ":
			info["error"] = str(result)[12:-1]
		else:
			info["error"] = "Unknown server error"
	else:
		info = {
				'id': id,
				'status': status,
				'result': result,
			}

	if shouldReturnJson():
		return jsonify(info)
	else:
		r = request.args.get("r")
		if r is not None and status == "SUCCESS":
			return redirect(r)
		else:
			return render_template("tasks/view.html", info=info)
