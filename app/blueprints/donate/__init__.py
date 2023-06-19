# ContentDB
# Copyright (C) 2023 rubenwardy
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


from flask import Blueprint, render_template
from flask_login import current_user
from sqlalchemy import or_, and_

from app.models import User, Package, PackageState, db, License, PackageReview

bp = Blueprint("donate", __name__)


@bp.route("/donate/")
def donate():
	reviewed_packages = None
	if current_user.is_authenticated:
		reviewed_packages = Package.query.filter(
			Package.state == PackageState.APPROVED,
			Package.reviews.any(and_(PackageReview.author_id == current_user.id, PackageReview.rating >= 3)),
			or_(Package.donate_url.isnot(None), Package.author.has(User.donate_url.isnot(None)))
		).order_by(db.asc(Package.title)).all()

	query = Package.query.filter(
			Package.license.has(License.is_foss == True),
			Package.media_license.has(License.is_foss == True),
			Package.state == PackageState.APPROVED,
			or_(Package.donate_url.isnot(None), Package.author.has(User.donate_url.isnot(None)))
	).order_by(db.desc(Package.score))

	packages_count = query.count()
	top_packages = query.limit(40).all()

	return render_template("donate/index.html",
			reviewed_packages=reviewed_packages, top_packages=top_packages, packages_count=packages_count)
