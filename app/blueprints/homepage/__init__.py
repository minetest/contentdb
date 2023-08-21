# ContentDB
# Copyright (C) 2018-23 rubenwardy
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

from flask import Blueprint, render_template, redirect
from sqlalchemy import and_

from app.models import Package, PackageReview, Thread, User, PackageState, db, PackageType, PackageRelease, Tags, Tag, \
	Collection

bp = Blueprint("homepage", __name__)

from sqlalchemy.orm import joinedload, subqueryload
from sqlalchemy.sql.expression import func


@bp.route("/gamejam/")
def gamejam():
	return redirect("https://forum.minetest.net/viewtopic.php?t=28802")


@bp.route("/")
def home():
	def package_load(query):
		return query.options(
				joinedload(Package.author),
				subqueryload(Package.main_screenshot),
				subqueryload(Package.cover_image),
				joinedload(Package.license),
				joinedload(Package.media_license))

	def review_load(query):
		return query.options(
			joinedload(PackageReview.author),
			joinedload(PackageReview.thread).subqueryload(Thread.first_reply),
			joinedload(PackageReview.package).joinedload(Package.author).load_only(User.username, User.display_name),
			joinedload(PackageReview.package).load_only(Package.title, Package.name).subqueryload(Package.main_screenshot))

	query = Package.query.filter_by(state=PackageState.APPROVED)
	count = query.count()

	spotlight_pkgs = query.filter(
			Package.collections.any(and_(Collection.name == "spotlight", Collection.author.has(username="ContentDB")))) \
		.order_by(func.random()).limit(6).all()

	new = package_load(query.order_by(db.desc(Package.approved_at))).limit(4).all()
	pop_mod = package_load(query.filter_by(type=PackageType.MOD).order_by(db.desc(Package.score))).limit(8).all()
	pop_gam = package_load(query.filter_by(type=PackageType.GAME).order_by(db.desc(Package.score))).limit(8).all()
	pop_txp = package_load(query.filter_by(type=PackageType.TXP).order_by(db.desc(Package.score))).limit(8).all()
	high_reviewed = package_load(query.order_by(db.desc(Package.score - Package.score_downloads))) \
			.filter(Package.reviews.any()).limit(4).all()

	updated = package_load(db.session.query(Package).select_from(PackageRelease).join(Package)
			.filter_by(state=PackageState.APPROVED)
			.order_by(db.desc(PackageRelease.releaseDate))
			.limit(20)).all()
	updated = updated[:4]

	reviews = review_load(PackageReview.query.filter(PackageReview.rating > 3)
			.order_by(db.desc(PackageReview.created_at))).limit(5).all()

	downloads_result = db.session.query(func.sum(Package.downloads)).one_or_none()
	downloads = 0 if not downloads_result or not downloads_result[0] else downloads_result[0]

	tags = db.session.query(func.count(Tags.c.tag_id), Tag) \
		.select_from(Tag).outerjoin(Tags).join(Package).filter(Package.state == PackageState.APPROVED)\
		.group_by(Tag.id).order_by(db.asc(Tag.title)).all()

	return render_template("index.html", count=count, downloads=downloads, tags=tags, spotlight_pkgs=spotlight_pkgs,
			new=new, updated=updated, pop_mod=pop_mod, pop_txp=pop_txp, pop_gam=pop_gam, high_reviewed=high_reviewed,
			reviews=reviews)
