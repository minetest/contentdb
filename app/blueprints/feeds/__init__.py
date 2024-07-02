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


from flask import Blueprint, jsonify, render_template, make_response
from flask_babel import gettext

from app.markdown import render_markdown
from app.models import Package, PackageState, db, PackageRelease
from app.utils import is_package_page, abs_url_for

bp = Blueprint("feeds", __name__)


def _make_feed(title: str, feed_url: str, items: list):
	return {
		"version": "https://jsonfeeds.org/version/1",
		"title": title,
		"description": gettext("Welcome to the best place to find Minetest mods, games, and texture packs"),
		"home_page_url": "https://content.minetest.net/",
		"feed_url": feed_url,
		"icon": "https://content.minetest.net/favicon-128.png",
		"expired": False,
		"items": items,
	}


def _get_new_packages_feed(feed_url: str) -> dict:
	packages = (Package.query
		.filter(Package.state == PackageState.APPROVED)
		.order_by(db.desc(Package.approved_at))
		.limit(100)
		.all())

	items = [{
			"id": package.get_url("packages.view", absolute=True),
			"language": "en",
			"title": f"New: {package.title}",
			"content_html": render_markdown(package.desc) if package.desc else None,
			"author": package.author.display_name,
			"url": package.get_url("packages.view", absolute=True),
			"summary": package.short_desc,
			"date_published": package.approved_at.isoformat(timespec="seconds") + "Z",
			"tags": ["new_package"],
		} for package in packages]

	return _make_feed(gettext("ContentDB new packages"), feed_url, items)


def _get_releases_feed(query, feed_url: str):
	releases = (query
		.filter(PackageRelease.package.has(state=PackageState.APPROVED), PackageRelease.approved==True)
		.order_by(db.desc(PackageRelease.created_at))
		.limit(250)
		.all())

	items = [{
			"id": release.package.get_url("packages.view_release", id=release.id, absolute=True),
			"language": "en",
			"title": f"{release.title} - {release.package.title}",
			"content_html": render_markdown(release.release_notes) if release.release_notes else None,
			"author": release.package.author.display_name,
			"url": release.package.get_url("packages.view_release", id=release.id, absolute=True),
			"summary": release.summary,
			"date_published": release.created_at.isoformat(timespec="seconds") + "Z",
			"tags": ["release"],
		} for release in releases]

	return _make_feed(gettext("ContentDB package updates"), feed_url, items)


def _get_all_feed(feed_url: str):
	releases = _get_releases_feed(PackageRelease.query, "")["items"]
	packages = _get_new_packages_feed("")["items"]
	items = releases + packages

	return _make_feed(gettext("ContentDB all"), feed_url, items)


def _atomify(feed):
	resp = make_response(render_template("feeds/json_to_atom.xml", feed=feed))
	resp.headers["Content-type"] = "application/atom+xml; charset=utf-8"
	return resp


@bp.route("/feeds/all.json")
def all_json():
	feed = _get_all_feed(abs_url_for("feeds.all_json"))
	return jsonify(feed)


@bp.route("/feeds/all.atom")
def all_atom():
	feed = _get_all_feed(abs_url_for("feeds.all_atom"))
	return _atomify(feed)


@bp.route("/feeds/packages.json")
def packages_all_json():
	feed = _get_new_packages_feed(abs_url_for("feeds.packages_all_json"))
	return jsonify(feed)


@bp.route("/feeds/packages.atom")
def packages_all_atom():
	feed = _get_new_packages_feed(abs_url_for("feeds.packages_all_atom"))
	return _atomify(feed)


@bp.route("/feeds/releases.json")
def releases_all_json():
	feed = _get_releases_feed(PackageRelease.query, abs_url_for("feeds.releases_all_json"))
	return jsonify(feed)


@bp.route("/feeds/releases.atom")
def releases_all_atom():
	feed = _get_releases_feed(PackageRelease.query, abs_url_for("feeds.releases_all_atom"))
	return _atomify(feed)


@bp.route("/packages/<author>/<name>/releases_feed.json")
@is_package_page
def releases_package_json(package: Package):
	feed = _get_releases_feed(package.releases, package.get_url("feeds.releases_package_json", absolute=True))
	return jsonify(feed)


@bp.route("/packages/<author>/<name>/releases_feed.atom")
@is_package_page
def releases_package_atom(package: Package):
	feed = _get_releases_feed(package.releases, package.get_url("feeds.releases_package_atom", absolute=True))
	return _atomify(feed)
