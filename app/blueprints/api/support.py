from app.models import PackageRelease, db, Permission
from app.tasks.importtasks import makeVCSRelease
from celery import uuid
from flask import jsonify, make_response, url_for
import datetime


def error(status, message):
	return make_response(jsonify({ "success": False, "error": message }), status)


def handleCreateRelease(token, package, title, ref):
	if not token.canOperateOnPackage(package):
		return error(403, "API token does not have access to the package")

	if not package.checkPerm(token.owner, Permission.MAKE_RELEASE):
		return error(403, "Permission denied. Missing MAKE_RELEASE permission")

	five_minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=5)
	count = package.releases.filter(PackageRelease.releaseDate > five_minutes_ago).count()
	if count >= 2:
		return error(429, "Too many requests, please wait before trying again")

	rel = PackageRelease()
	rel.package = package
	rel.title   = title
	rel.url     = ""
	rel.task_id = uuid()
	rel.min_rel = None
	rel.max_rel = None
	db.session.add(rel)
	db.session.commit()

	makeVCSRelease.apply_async((rel.id, ref), task_id=rel.task_id)

	return jsonify({
		"success": True,
		"task": url_for("tasks.check", id=rel.task_id),
		"release": rel.getAsDictionary()
	})
