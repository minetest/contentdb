from flask import *
from flask_user import *
from flask.ext import menu
from app import app
from app.models import *
from app.tasks import celery
from app.tasks.importtasks import getMeta
# from celery.result import AsyncResult

from .utils import *

@app.route("/tasks/getmeta/new/")
def new_getmeta_page():
	aresult = getMeta.delay(request.args.get("url"))
	return jsonify({
		"poll_url": url_for("check_task", id=aresult.id),
	})

@app.route("/tasks/<id>/")
def check_task(id):
    result = celery.AsyncResult(id)
    status = result.status
    traceback = result.traceback
    result = result.result
    if isinstance(result, Exception):
        return jsonify({
            'status': status,
            'error': str(result),
            # 'traceback': traceback,
        })
    else:
        return jsonify({
            'status': status,
            'result': result,
        })
