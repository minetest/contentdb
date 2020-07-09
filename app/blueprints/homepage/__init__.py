from flask import Blueprint, render_template

bp = Blueprint("homepage", __name__)

from app.models import *
import flask_menu as menu
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import func

@bp.route("/")
@menu.register_menu(bp, ".", "Home")
def home():
	def join(query):
		return query.options( \
			joinedload(Package.license), \
			joinedload(Package.media_license))

	query   = Package.query.filter_by(approved=True, soft_deleted=False)
	count   = query.count()
	new     = join(query.order_by(db.desc(Package.created_at))).limit(8).all()
	pop_mod = join(query.filter_by(type=PackageType.MOD).order_by(db.desc(Package.score))).limit(8).all()
	pop_gam = join(query.filter_by(type=PackageType.GAME).order_by(db.desc(Package.score))).limit(4).all()
	pop_txp = join(query.filter_by(type=PackageType.TXP).order_by(db.desc(Package.score))).limit(4).all()
	downloads_result = db.session.query(func.sum(Package.downloads)).one_or_none()
	downloads = 0 if not downloads_result or not downloads_result[0] else downloads_result[0]
	return render_template("index.html", count=count, downloads=downloads, \
			new=new, pop_mod=pop_mod, pop_txp=pop_txp, pop_gam=pop_gam)
