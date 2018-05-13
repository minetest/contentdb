from flask import *
from flask_user import *
from flask.ext import menu
from app import app, csrf
from app.models import *
from app.tasks import celery
from app.tasks.importtasks import getMeta
from .utils import shouldReturnJson
# from celery.result import AsyncResult

from .utils import *

@csrf.exempt
@app.route("/tasks/getmeta/new/", methods=["POST"])
@login_required
def new_getmeta_page():
	author = request.args.get("author")
	author = current_user.forums_username if author is None else author
	aresult = getMeta.delay(request.args.get("url"), author)
	return jsonify({
		"poll_url": url_for("check_task", id=aresult.id),
	})

@app.route("/tasks/<id>/")
@login_required
def check_task(id):
	result = celery.AsyncResult(id)
	status = result.status
	traceback = result.traceback
	result = result.result

	info = None
	if isinstance(result, Exception):
		info = {
				'id': id,
				'status': status,
				'error': str(result),
			}
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
		if r is None:
			abort(422)

		if status == "SUCCESS":
			flash("Task complete!", "success")
			return redirect(r)
		else:
			return render_template("tasks/view.html", info=info)
