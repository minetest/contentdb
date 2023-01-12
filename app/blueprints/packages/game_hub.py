# ContentDB
# Copyright (C) 2022 rubenwardy
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

from flask import render_template, abort
from sqlalchemy.orm import joinedload

from . import bp
from app.utils import is_package_page
from ...models import Package, PackageType, PackageState, db, PackageRelease


@bp.route("/packages/<author>/<name>/hub/")
@is_package_page
def game_hub(package: Package):
	if package.type != PackageType.GAME:
		abort(404)

	def join(query):
		return query.options(
			joinedload(Package.license),
			joinedload(Package.media_license))

	query = Package.query.filter(Package.supported_games.any(game=package), Package.state==PackageState.APPROVED)
	count = query.count()

	new = join(query.order_by(db.desc(Package.approved_at))).limit(4).all()
	pop_mod = join(query.filter_by(type=PackageType.MOD).order_by(db.desc(Package.score))).limit(8).all()
	pop_txp = join(query.filter_by(type=PackageType.TXP).order_by(db.desc(Package.score))).limit(8).all()
	high_reviewed = join(query.order_by(db.desc(Package.score - Package.score_downloads))) \
		.filter(Package.reviews.any()).limit(4).all()

	updated = db.session.query(Package).select_from(PackageRelease).join(Package) \
		.filter(Package.supported_games.any(game=package), Package.state==PackageState.APPROVED) \
		.order_by(db.desc(PackageRelease.releaseDate)) \
		.limit(20).all()
	updated = updated[:4]

	return render_template("packages/game_hub.html", package=package, count=count,
			new=new, updated=updated, pop_mod=pop_mod, pop_txp=pop_txp,
			high_reviewed=high_reviewed)
