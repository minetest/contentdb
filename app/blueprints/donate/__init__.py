from flask import Blueprint, render_template
from flask_login import current_user
from sqlalchemy import or_

from app.models import User, Package, PackageState, db, License

bp = Blueprint("donate", __name__)


@bp.route("/donate/")
def donate():
	reviewed_packages = None
	if current_user.is_authenticated:
		reviewed_packages = Package.query.filter(
			Package.state == PackageState.APPROVED,
			Package.reviews.any(author_id=current_user.id, recommends=True),
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
