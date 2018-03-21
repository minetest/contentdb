from flask import *
from flask_user import *
from flask.ext import menu
from app import app
from app.models import *

from flask_wtf import FlaskForm
from wtforms import *


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


def getPageByInfo(type, author, name):
	user = User.query.filter_by(username=author).first()
	if user is None:
		abort(404)

	package = Package.query.filter_by(name=name, author_id=user.id,
			type=PackageType[type.upper()]).first()
	if package is None:
		abort(404)

	return package

def getReleases(package):
	if package.checkPerm(current_user, Permission.MAKE_RELEASE):
		return package.releases
	else:
		return [rel for rel in package.releases if rel.approved]


@app.route("/<type>s/<author>/<name>/")
def package_page(type, author, name):
	package = getPageByInfo(type, author, name)
	releases = getReleases(package)

	return render_template('package_details.html', package=package, releases=releases)


class PackageForm(FlaskForm):
	name         = StringField("Name")
	title        = StringField("Title")
	shortDesc    = StringField("Short Description")
	desc         = StringField("Long Description")
	type         = SelectField("Type", choices=PackageType.choices(), coerce=PackageType.coerce, default=PackageType.MOD)
	repo         = StringField("Repo URL")
	website      = StringField("Website URL")
	issueTracker = StringField("Issue Tracker URL")
	forums       = StringField("Forum Topic ID")
	submit       = SubmitField('Save')

@menu.register_menu(app, '.new', 'Create', order=20)
@app.route("/new/", methods=['GET', 'POST'])
@app.route("/<type>s/<author>/<name>/edit/", methods=['GET', 'POST'])
@login_required
def create_edit_package_page(type=None, author=None, name=None):
	package = None
	form = None
	if type is None:
		form = PackageForm(formdata=request.form)
	else:
		package = getPageByInfo(type, author, name)
		if not package.checkPerm(current_user, Permission.EDIT_PACKAGE):
			return redirect(package.getDetailsURL())

		form = PackageForm(formdata=request.form, obj=package)

	# Initial form class from post data and default data
	if request.method == "POST" and form.validate():
		# Successfully submitted!
		if not package:
			package = Package()
			package.author = current_user

		form.populate_obj(package) # copy to row
		db.session.commit() # save
		return redirect(package.getDetailsURL()) # redirect

	return render_template('package_create_edit.html', package=package, form=form)


class CreatePackageReleaseForm(FlaskForm):
	name         = StringField("Name")
	title        = StringField("Title")
	uploadOpt    = RadioField ("File", choices=[("vcs", "From VCS Commit or Branch"), ("upload", "File Upload")])
	vcsLabel     = StringField("VCS Commit or Branch", default="master")
	fileUpload   = FileField("File Upload")
	submit       = SubmitField('Save')

class EditPackageReleaseForm(FlaskForm):
	name         = StringField("Name")
	title        = StringField("Title")
	url          = StringField("URL")
	approved     = BooleanField("Is Approved")
	submit       = SubmitField('Save')

@app.route("/<type>s/<author>/<name>/releases/new/", methods=['GET', 'POST'])
@login_required
def create_release_page(type, author, name):
	package = getPageByInfo(type, author, name)
	if not package.checkPerm(current_user, Permission.MAKE_RELEASE):
		return redirect(package.getDetailsURL())

	# Initial form class from post data and default data
	form = CreatePackageReleaseForm(formdata=request.form)
	if request.method == "POST" and form.validate():
		if form["uploadOpt"].data == "vcs":
			rel = PackageRelease()
			rel.package = package
			rel.title = form["title"].data
			rel.url = form["vcsLabel"].data
			# TODO: get URL to commit from branch name
			db.session.commit()
			return redirect(package.getDetailsURL()) # redirect
		else:
			raise Exception("Unimplemented option = file upload")

	return render_template('package_release_new.html', package=package, form=form)

@app.route("/<type>s/<author>/<name>/releases/<id>/", methods=['GET', 'POST'])
@login_required
def edit_release_page(type, author, name, id):
	user = User.query.filter_by(username=author).first()
	if user is None:
		abort(404)

	release = PackageRelease.query.filter_by(id=id).first()
	if release is None:
		abort(404)

	package = release.package
	if package.name != name or package.type != PackageType[type.upper()]:
		abort(404)

	canEdit    = package.checkPerm(current_user, Permission.MAKE_RELEASE)
	canApprove = package.checkPerm(current_user, Permission.APPROVE_RELEASE)
	if not (canEdit or canApprove):
		return redirect(package.getDetailsURL())

	# Initial form class from post data and default data
	form = EditPackageReleaseForm(formdata=request.form, obj=release)
	if request.method == "POST" and form.validate():
		wasApproved = release.approved
		if canEdit:
			release.title = form["title"].data

		if package.checkPerm(current_user, Permission.CHANGE_RELEASE_URL):
			release.url = form["url"].data

		if canApprove:
			release.approved = form["approved"].data
		else:
			release.approved = wasApproved

		db.session.commit()
		return redirect(package.getDetailsURL())

	return render_template('package_release_edit.html', package=package, form=form)
