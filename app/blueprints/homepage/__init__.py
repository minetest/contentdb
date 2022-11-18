from flask import Blueprint, render_template, redirect

bp = Blueprint("homepage", __name__)

from app.models import *
from sqlalchemy.orm import joinedload, subqueryload, contains_eager
from sqlalchemy.sql.expression import func


GAMEJAM_BANNER = "https://raw.githubusercontent.com/GreenXenith/minetestgamejam/master/2022/images/banner_textless.png"


class GameJam:
	cover_image = type("", (), dict(url=GAMEJAM_BANNER))()
	tags = []

	def getCoverImageURL(self):
		return GAMEJAM_BANNER

	def getURL(self, _name):
		return "/gamejam/"

	title = "Minetest Game Jam 2022"
	author = None

	short_desc = "It's back! We're holding a 3-week Game Jam starting November 1st. Sharpen your gamedev skills with a " \
				 "chance for cash prizes. "
	type = type("", (), dict(value="Competition"))()
	content_warnings = []
	reviews = []


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
			joinedload(PackageReview.thread).joinedload(Thread.first_reply),
			joinedload(PackageReview.package).joinedload(Package.author).load_only(User.username, User.display_name),
			joinedload(PackageReview.package).load_only(Package.title, Package.name).subqueryload(Package.main_screenshot))

	query   = Package.query.filter_by(state=PackageState.APPROVED)
	count   = query.count()

	featured = query.filter(Package.tags.any(name="featured")).order_by(func.random()).limit(6).all()
	featured.insert(0, GameJam())

	new     = package_load(query.order_by(db.desc(Package.approved_at))).limit(4).all()
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

	reviews = review_load(PackageReview.query.filter_by(recommends=True).order_by(db.desc(PackageReview.created_at))).limit(5).all()

	downloads_result = db.session.query(func.sum(Package.downloads)).one_or_none()
	downloads = 0 if not downloads_result or not downloads_result[0] else downloads_result[0]

	tags = db.session.query(func.count(Tags.c.tag_id), Tag) \
		.select_from(Tag).outerjoin(Tags).group_by(Tag.id).order_by(db.asc(Tag.title)).all()

	return render_template("index.html", count=count, downloads=downloads, tags=tags, featured=featured,
			new=new, updated=updated, pop_mod=pop_mod, pop_txp=pop_txp, pop_gam=pop_gam, high_reviewed=high_reviewed, reviews=reviews)
