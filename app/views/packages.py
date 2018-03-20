from flask import *
from flask_user import *
from flask.ext import menu
from app import app
from app.models import *


# TODO: the following could be made into one route, except I'm not sure how
# to do the menu

@app.route('/mods/')
@menu.register_menu(app, '.mods', 'Mods', order=10)
def mods_page():
	packages = Package.query.filter_by(type=PackageType.MOD).all()
	return render_template('packages.html', title="Mods", packages=packages)

@app.route('/games/')
@menu.register_menu(app, '.games', 'Games', order=11)
def games_page():
	packages = Package.query.filter_by(type=PackageType.GAME).all()
	return render_template('packages.html', title="Games", packages=packages)

@app.route('/texturepacks/')
@menu.register_menu(app, '.txp', 'Texture Packs', order=12)
def txp_page():
	packages = Package.query.filter_by(type=PackageType.TXP).all()
	return render_template('packages.html', title="Texture Packs", packages=packages)



@app.route("/<type>s/<author>/<name>/")
def package_page(type, author, name):
	user = User.query.filter_by(username=author).first()
	if user is None:
		abort(404)

	package = Package.query.filter_by(name=name, author_id=user.id,
			type=PackageType.fromName(type)).first()
	if package is None:
		abort(404)

	return render_template('package_details.html', package=package)
