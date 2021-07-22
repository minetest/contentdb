# ContentDB
# Copyright (C) 2018-21  rubenwardy
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

from flask import request, jsonify, current_app
from flask_login import current_user, login_required
from sqlalchemy.sql.expression import func

from app import csrf
from app.utils.markdown import render_markdown
from app.models import Tag, PackageState, PackageType, Package, db, PackageRelease, Permission, ForumTopic, MinetestRelease, APIToken, PackageScreenshot, License, ContentWarning, User
from app.querybuilder import QueryBuilder
from app.utils import is_package_page, get_int_or_abort
from . import bp
from .auth import is_api_authd
from .support import error, api_create_vcs_release, api_create_zip_release, api_create_screenshot, api_order_screenshots, api_edit_package


@bp.route("/api/packages/")
def packages():
	qb    = QueryBuilder(request.args)
	query = qb.buildPackageQuery()

	if request.args.get("fmt") == "keys":
		return jsonify([package.getAsDictionaryKey() for package in query.all()])

	pkgs = qb.convertToDictionary(query.all())
	if "engine_version" in request.args or "protocol_version" in request.args:
		pkgs = [package for package in pkgs if package.get("release")]
	return jsonify(pkgs)


@bp.route("/api/packages/<author>/<name>/")
@is_package_page
def package(package):
	return jsonify(package.getAsDictionary(current_app.config["BASE_URL"]))


@bp.route("/api/packages/<author>/<name>/", methods=["PUT"])
@csrf.exempt
@is_package_page
@is_api_authd
def edit_package(token, package):
	if not token:
		error(401, "Authentication needed")

	return api_edit_package(token, package, request.json)


def resolve_package_deps(out, package, only_hard, depth=1):
	id = package.getId()
	if id in out:
		return

	ret = []
	out[id] = ret

	if package.type != PackageType.MOD:
		return

	for dep in package.dependencies:
		if only_hard and dep.optional:
			continue

		if dep.package:
			name = dep.package.name
			fulfilled_by = [ dep.package.getId() ]
			resolve_package_deps(out, dep.package, only_hard, depth)

		elif dep.meta_package:
			name = dep.meta_package.name
			fulfilled_by = [ pkg.getId() for pkg in dep.meta_package.packages]

			if depth == 1:
				most_likely = next((pkg for pkg in dep.meta_package.packages if pkg.type == PackageType.MOD), None)
				if most_likely:
					resolve_package_deps(out, most_likely, only_hard, depth + 1)

		else:
			raise Exception("Malformed dependency")

		ret.append({
			"name": name,
			"is_optional": dep.optional,
			"packages": fulfilled_by
		})


@bp.route("/api/packages/<author>/<name>/dependencies/")
@is_package_page
def package_dependencies(package):
	only_hard = request.args.get("only_hard")

	out = {}
	resolve_package_deps(out, package, only_hard)

	return jsonify(out)


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
		error(400, "Missing topic ID or discard bool")

	topic = ForumTopic.query.get(tid)
	if not topic.checkPerm(current_user, Permission.TOPIC_DISCARD):
		error(403, "Permission denied, need: TOPIC_DISCARD")

	topic.discarded = discard == "true"
	db.session.commit()

	return jsonify(topic.getAsDictionary())


@bp.route("/api/whoami/")
@is_api_authd
def whoami(token):
	if token is None:
		return jsonify({ "is_authenticated": False, "username": None })
	else:
		return jsonify({ "is_authenticated": True, "username": token.owner.username })


@bp.route("/api/markdown/", methods=["POST"])
@csrf.exempt
def markdown():
	return render_markdown(request.data.decode("utf-8"))


@bp.route("/api/releases/")
def list_all_releases():
	query = PackageRelease.query.filter_by(approved=True) \
			.filter(PackageRelease.package.has(state=PackageState.APPROVED)) \
			.order_by(db.desc(PackageRelease.releaseDate))

	if "author" in request.args:
		author = User.query.filter_by(username=request.args["author"]).first()
		if author is None:
			error(404, "Author not found")
		query = query.filter(PackageRelease.package.has(author=author))

	if "maintainer" in request.args:
		maintainer = User.query.filter_by(username=request.args["maintainer"]).first()
		if maintainer is None:
			error(404, "Maintainer not found")
		query = query.join(Package)
		query = query.filter(Package.maintainers.any(id=maintainer.id))

	return jsonify([ rel.getLongAsDictionary() for rel in query.limit(30).all() ])


@bp.route("/api/packages/<author>/<name>/releases/")
@is_package_page
def list_releases(package):
	return jsonify([ rel.getAsDictionary() for rel in package.releases.all() ])


@bp.route("/api/packages/<author>/<name>/releases/new/", methods=["POST"])
@csrf.exempt
@is_package_page
@is_api_authd
def create_release(token, package):
	if not token:
		error(401, "Authentication needed")

	if not package.checkPerm(token.owner, Permission.APPROVE_RELEASE):
		error(403, "You do not have the permission to approve releases")

	data = request.json or request.form
	if "title" not in data:
		error(400, "Title is required in the POST data")

	if data.get("method") == "git":
		for option in ["method", "ref"]:
			if option not in data:
				error(400, option + " is required in the POST data")

		return api_create_vcs_release(token, package, data["title"], data["ref"])

	elif request.files:
		file = request.files.get("file")
		if file is None:
			error(400, "Missing 'file' in multipart body")

		commit_hash = data.get("commit")

		return api_create_zip_release(token, package, data["title"], file, None, None, "API", commit_hash)

	else:
		error(400, "Unknown release-creation method. Specify the method or provide a file.")


@bp.route("/api/packages/<author>/<name>/releases/<int:id>/")
@is_package_page
def release(package: Package, id: int):
	release = PackageRelease.query.get(id)
	if release is None or release.package != package:
		error(404, "Release not found")

	return jsonify(release.getAsDictionary())


@bp.route("/api/packages/<author>/<name>/releases/<int:id>/", methods=["DELETE"])
@csrf.exempt
@is_package_page
@is_api_authd
def delete_release(token: APIToken, package: Package, id: int):
	release = PackageRelease.query.get(id)
	if release is None or release.package != package:
		error(404, "Release not found")

	if not token:
		error(401, "Authentication needed")

	if not token.canOperateOnPackage(package):
		error(403, "API token does not have access to the package")

	if not release.checkPerm(token.owner, Permission.DELETE_RELEASE):
		error(403, "Unable to delete the release, make sure there's a newer release available")

	db.session.delete(release)
	db.session.commit()

	return jsonify({"success": True})


@bp.route("/api/packages/<author>/<name>/screenshots/")
@is_package_page
def list_screenshots(package):
	screenshots = package.screenshots.all()
	return jsonify([ss.getAsDictionary(current_app.config["BASE_URL"]) for ss in screenshots])


@bp.route("/api/packages/<author>/<name>/screenshots/new/", methods=["POST"])
@csrf.exempt
@is_package_page
@is_api_authd
def create_screenshot(token: APIToken, package: Package):
	if not token:
		error(401, "Authentication needed")

	if not package.checkPerm(token.owner, Permission.ADD_SCREENSHOTS):
		error(403, "You do not have the permission to create screenshots")

	data = request.form
	if "title" not in data:
		error(400, "Title is required in the POST data")

	file = request.files.get("file")
	if file is None:
		error(400, "Missing 'file' in multipart body")

	return api_create_screenshot(token, package, data["title"], file)


@bp.route("/api/packages/<author>/<name>/screenshots/<int:id>/")
@is_package_page
def screenshot(package, id):
	ss = PackageScreenshot.query.get(id)
	if ss is None or ss.package != package:
		error(404, "Screenshot not found")

	return jsonify(ss.getAsDictionary(current_app.config["BASE_URL"]))


@bp.route("/api/packages/<author>/<name>/screenshots/<int:id>/", methods=["DELETE"])
@csrf.exempt
@is_package_page
@is_api_authd
def delete_screenshot(token: APIToken, package: Package, id: int):
	ss = PackageScreenshot.query.get(id)
	if ss is None or ss.package != package:
		error(404, "Screenshot not found")

	if not token:
		error(401, "Authentication needed")

	if not package.checkPerm(token.owner, Permission.ADD_SCREENSHOTS):
		error(403, "You do not have the permission to delete screenshots")

	if not token.canOperateOnPackage(package):
		error(403, "API token does not have access to the package")

	if package.cover_image == ss:
		package.cover_image = None
		db.session.merge(package)

	db.session.delete(ss)
	db.session.commit()

	return jsonify({ "success": True })


@bp.route("/api/packages/<author>/<name>/screenshots/order/", methods=["POST"])
@csrf.exempt
@is_package_page
@is_api_authd
def order_screenshots(token: APIToken, package: Package):
	if not token:
		error(401, "Authentication needed")

	if not package.checkPerm(token.owner, Permission.ADD_SCREENSHOTS):
		error(403, "You do not have the permission to delete screenshots")

	if not token.canOperateOnPackage(package):
		error(403, "API token does not have access to the package")

	json = request.json
	if json is None or not isinstance(json, list):
		error(400, "Expected order body to be array")

	return api_order_screenshots(token, package, request.json)


@bp.route("/api/scores/")
def package_scores():
	qb    = QueryBuilder(request.args)
	query = qb.buildPackageQuery()

	pkgs = [package.getScoreDict() for package in query.all()]
	return jsonify(pkgs)


@bp.route("/api/tags/")
def tags():
	return jsonify([tag.getAsDictionary() for tag in Tag.query.all() ])


@bp.route("/api/content_warnings/")
def content_warnings():
	return jsonify([warning.getAsDictionary() for warning in ContentWarning.query.all() ])


@bp.route("/api/licenses/")
def licenses():
	return jsonify([ { "name": license.name, "is_foss": license.is_foss } \
		for license in License.query.order_by(db.asc(License.name)).all() ])


@bp.route("/api/homepage/")
def homepage():
	query   = Package.query.filter_by(state=PackageState.APPROVED)
	count   = query.count()

	featured = Package.query.filter(Package.tags.any(name="featured")).order_by(
			func.random()).limit(6).all()
	new     = query.order_by(db.desc(Package.approved_at)).limit(4).all()
	pop_mod = query.filter_by(type=PackageType.MOD).order_by(db.desc(Package.score)).limit(8).all()
	pop_gam = query.filter_by(type=PackageType.GAME).order_by(db.desc(Package.score)).limit(8).all()
	pop_txp = query.filter_by(type=PackageType.TXP).order_by(db.desc(Package.score)).limit(8).all()
	high_reviewed = query.order_by(db.desc(Package.score - Package.score_downloads)) \
			.filter(Package.reviews.any()).limit(4).all()

	updated = db.session.query(Package).select_from(PackageRelease).join(Package) \
			.filter_by(state=PackageState.APPROVED) \
			.order_by(db.desc(PackageRelease.releaseDate)) \
			.limit(20).all()
	updated = updated[:4]

	downloads_result = db.session.query(func.sum(Package.downloads)).one_or_none()
	downloads = 0 if not downloads_result or not downloads_result[0] else downloads_result[0]

	def mapPackages(packages):
		return [pkg.getAsDictionaryKey() for pkg in packages]

	return {
		"count": count,
		"downloads": downloads,
		"featured": featured,
		"new": mapPackages(new),
		"updated": mapPackages(updated),
		"pop_mod": mapPackages(pop_mod),
		"pop_txp": mapPackages(pop_txp),
		"pop_game": mapPackages(pop_gam),
		"high_reviewed": mapPackages(high_reviewed)
	}


@bp.route("/api/minetest_versions/")
def versions():
	protocol_version = request.args.get("protocol_version")
	engine_version = request.args.get("engine_version")
	if protocol_version or engine_version:
		rel = MinetestRelease.get(engine_version, get_int_or_abort(protocol_version))
		if rel is None:
			error(404, "No releases found")

		return jsonify(rel.getAsDictionary())

	return jsonify([rel.getAsDictionary() \
			for rel in MinetestRelease.query.all() if rel.getActual() is not None])
