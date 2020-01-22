# Content DB
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


from flask import *
from flask_user import *
from . import bp
from .auth import is_api_authd
from app import csrf
from app.models import *
from app.utils import is_package_page
from app.markdown import render_markdown
from app.querybuilder import QueryBuilder

@bp.route("/api/packages/")
def packages():
	qb    = QueryBuilder(request.args)
	query = qb.buildPackageQuery()
	ver   = qb.getMinetestVersion()

	pkgs = [package.getAsDictionaryShort(current_app.config["BASE_URL"], version=ver) \
			for package in query.all()]
	return jsonify(pkgs)


@bp.route("/api/packages/<author>/<name>/")
@is_package_page
def package(package):
	return jsonify(package.getAsDictionary(current_app.config["BASE_URL"]))


@bp.route("/api/packages/<author>/<name>/dependencies/")
@is_package_page
def package_dependencies(package):
	ret = []

	for dep in package.dependencies:
		name = None
		fulfilled_by = None

		if dep.package:
			name = dep.package.name
			fulfilled_by = [ dep.package.getAsDictionaryKey() ]

		elif dep.meta_package:
			name = dep.meta_package.name
			fulfilled_by = [ pkg.getAsDictionaryKey() for pkg in dep.meta_package.packages]

		else:
			raise "Malformed dependency"

		ret.append({
			"name": name,
			"is_optional": dep.optional,
			"packages": fulfilled_by
		})

	return jsonify(ret)


@bp.route("/api/topics/")
def topics():
	qb     = QueryBuilder(request.args)
	query  = qb.buildTopicQuery(show_added=True)
	return jsonify([t.getAsDictionary() for t in query.all()])


@bp.route("/api/topic_discard/", methods=["POST"])
@login_required
def topic_set_discard():
	tid = request.args.get("tid")
	discard = request.args.get("discard")
	if tid is None or discard is None:
		abort(400)

	topic = ForumTopic.query.get(tid)
	if not topic.checkPerm(current_user, Permission.TOPIC_DISCARD):
		abort(403)

	topic.discarded = discard == "true"
	db.session.commit()

	return jsonify(topic.getAsDictionary())


@bp.route("/api/minetest_versions/")
def versions():
	return jsonify([{ "name": rel.name, "protocol_version": rel.protocol }\
			for rel in MinetestRelease.query.all() if rel.getActual() is not None])


@bp.route("/api/whoami/")
@is_api_authd
def whoami(token):
	if token is None:
		return jsonify({ "is_authenticated": False, "username": None })
	else:
		return jsonify({ "is_authenticated": True, "username": token.owner.username })


@bp.route("/api/markdown/", methods=["POST"])
@csrf.exempt
def clean_markdown():
	return render_markdown(request.data.decode("utf-8"))
