from flask import *
from flask_user import *
from flask.ext import menu
from app import app
from app.models import *

@app.route('/mods/')
@menu.register_menu(app, '.mods', 'Mods')
def mods_page():
	packages = Package.query.filter_by(type=PackageType.MOD).all()
	return render_template('packages.html', title="Mods", packages=packages)

@app.route('/games/')
@menu.register_menu(app, '.games', 'Games')
def games_page():
	packages = Package.query.filter_by(type=PackageType.GAME).all()
	return render_template('packages.html', title="Games", packages=packages)

@app.route('/texturepacks/')
@menu.register_menu(app, '.txp', 'Texture Packs')
def txp_page():
	packages = Package.query.filter_by(type=PackageType.TXP).all()
	return render_template('packages.html', title="Texture Packs", packages=packages)

@app.route("/<type>s/<author>/<name>/")
def package_page(type, author, name):
	package = Package.query.filter_by(name=name).first()
	if package is None:
		abort(404)

	return render_template('package_details.html', package=package)
