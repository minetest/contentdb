from flask import *
from flask_user import *
from flask.ext import menu
from app import app
from app.models import *

@app.route('/mods/')
@menu.register_menu(app, '.mods', 'Mods')
def mods_page():
	packages = Package.query.all()
	return render_template('packages.html', title="Mods", packages=packages)

@app.route("/<type>s/<author>/<name>/")
def package_page(type, author, name):
	package = Package.query.filter_by(name=name).first()
	if package is None:
		abort(404)

	return render_template('package_details.html', package=package)
