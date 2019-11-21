from flask import Blueprint, render_template

bp = Blueprint("homepage", __name__)

from app.models import *
import flask_menu as menu
from sqlalchemy.sql.expression import func

@bp.route("/")
@menu.register_menu(bp, ".", "Home")
def home():
	query   = Package.query.filter_by(approved=True, soft_deleted=False)
	count   = query.count()
	new     = query.order_by(db.desc(Package.created_at)).limit(8).all()
	pop_mod = query.filter_by(type=PackageType.MOD).order_by(db.desc(Package.score)).limit(8).all()
	pop_gam = query.filter_by(type=PackageType.GAME).order_by(db.desc(Package.score)).limit(4).all()
	pop_txp = query.filter_by(type=PackageType.TXP).order_by(db.desc(Package.score)).limit(4).all()
	downloads = db.session.query(func.sum(PackageRelease.downloads)).first()[0]
	return render_template("index.html", count=count, downloads=downloads, \
			new=new, pop_mod=pop_mod, pop_txp=pop_txp, pop_gam=pop_gam)
