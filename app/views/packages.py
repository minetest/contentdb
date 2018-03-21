from flask import *
from flask_user import *
from flask.ext import menu
from app import app
from app.models import *

from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *


# TODO: the following could be made into one route, except I'm not sure how
# to do the menu

def doPackageList(type):
	title = "Packages"
	query = Package.query

	if type is not None:
		title = type.value + "s"
		query = query.filter_by(type=type, approved=True)

	search = request.args.get("q")
	if search is not None:
		query = query.filter(Package.title.contains(search))

	return render_template('packages.html', title=title, packages=query.all(), query=search)

@app.route('/packages/')
def packages_page():
	return doPackageList(None)

@app.route('/mods/')
@menu.register_menu(app, '.mods', 'Mods', order=11)
def mods_page():
	return doPackageList(PackageType.MOD)

@app.route('/games/')
@menu.register_menu(app, '.games', 'Games', order=12)
def games_page():
	return doPackageList(PackageType.GAME)

@app.route('/texturepacks/')
@menu.register_menu(app, '.txp', 'Texture Packs', order=13)
def txp_page():
	return doPackageList(PackageType.TXP)

def canSeeWorkQueue():
	return Permission.APPROVE_NEW.check(current_user) or \
		Permission.APPROVE_RELEASE.check(current_user) or \
			Permission.APPROVE_CHANGES.check(current_user)

@menu.register_menu(app, '.todo', "Work Queue", order=20, visible_when=canSeeWorkQueue)
@app.route("/todo/")
@login_required
def todo_page():
	canApproveNew = Permission.APPROVE_NEW.check(current_user)
	canApproveRel = Permission.APPROVE_RELEASE.check(current_user)

	packages = None
	if canApproveNew:
		packages = Package.query.filter_by(approved=False).all()

	releases = None
	if canApproveRel:
		releases = PackageRelease.query.filter_by(approved=False).all()

	return render_template('todo.html', title="Reports and Work Queue",
		approve_new=packages, releases=releases,
		canApproveNew=canApproveNew, canApproveRel=canApproveRel)


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
	name         = StringField("Name", [InputRequired(), Length(1, 20), Regexp("^[a-z0-9_]", 0, "Lower case letters (a-z), digits (0-9), and underscores (_) only")])
	title        = StringField("Title", [InputRequired(), Length(3, 50)])
	shortDesc    = StringField("Short Description", [InputRequired(), Length(1,200)])
	desc         = TextAreaField("Long Description", [Optional(), Length(0,10000)])
	type         = SelectField("Type", [InputRequired()], choices=PackageType.choices(), coerce=PackageType.coerce, default=PackageType.MOD)
	repo         = StringField("Repo URL", [Optional(), URL()])
	website      = StringField("Website URL", [Optional(), URL()])
	issueTracker = StringField("Issue Tracker URL", [Optional(), URL()])
	forums       = IntegerField("Forum Topic ID", [InputRequired(), NumberRange(0,999999)])
	submit       = SubmitField('Save')

@menu.register_menu(app, '.new', 'Create', order=21, visible_when=lambda: current_user.is_authenticated)
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
			# package.approved = package.checkPerm(current_user, Permission.APPROVE_NEW)

		form.populate_obj(package) # copy to row
		db.session.commit() # save
		return redirect(package.getDetailsURL()) # redirect

	return render_template('package_create_edit.html', package=package, form=form)

@app.route("/<type>s/<author>/<name>/approve/")
@login_required
def approve_package_page(type=None, author=None, name=None):
	package = getPageByInfo(type, author, name)

	if not package.checkPerm(current_user, Permission.APPROVE_NEW):
		flash("You don't have permission to do that.", "error")

	elif package.approved:
		flash("Package has already been approved", "error")

	else:
		package.approved = True
		db.session.commit()


	return redirect(package.getDetailsURL())

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
	url          = StringField("URL", [URL])
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

	return render_template('package_release_edit.html', package=package, release=release, form=form)
