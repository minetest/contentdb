from flask import *
from flask_user import *
from flask.ext import menu
from app import app
from app.models import *

from .utils import *

from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *


# TODO: the following could be made into one route, except I"m not sure how
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

	if shouldReturnJson():
		return jsonify([package.getAsDictionary(request.url_root) for package in query.all()])
	else:
		return render_template("packages/list.html", title=title, packages=query.all(), query=search)


@app.route("/packages/")
def packages_page():
	type = None
	typeStr = request.args.get("type")
	if typeStr is not None:
		type = PackageType[typeStr.upper()]
	return doPackageList(type)

@app.route("/mods/")
@menu.register_menu(app, ".mods", "Mods", order=11)
def mods_page():
	return doPackageList(PackageType.MOD)

@app.route("/games/")
@menu.register_menu(app, ".games", "Games", order=12)
def games_page():
	return doPackageList(PackageType.GAME)

@app.route("/texturepacks/")
@menu.register_menu(app, ".txp", "Texture Packs", order=13)
def txp_page():
	return doPackageList(PackageType.TXP)

def canSeeWorkQueue():
	return Permission.APPROVE_NEW.check(current_user) or \
		Permission.APPROVE_RELEASE.check(current_user) or \
			Permission.APPROVE_CHANGES.check(current_user)

@menu.register_menu(app, ".todo", "Work Queue", order=20, visible_when=canSeeWorkQueue)
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

	return render_template("todo.html", title="Reports and Work Queue",
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

	if shouldReturnJson():
		return jsonify(package.getAsDictionary(request.url_root))
	else:
		releases = getReleases(package)
		return render_template("packages/view.html", package=package, releases=releases)


@app.route("/<type>s/<author>/<name>/download/")
def package_download_page(type, author, name):
	package = getPageByInfo(type, author, name)
	release = package.getDownloadRelease()

	if release is None:
		if "application/zip" in request.accept_mimetypes and \
				not "text/html" in request.accept_mimetypes:
			return "", 204
		else:
			flash("No download available.", "error")
			return redirect(package.getDetailsURL())
	else:
		return redirect(release.url, code=302)


class PackageForm(FlaskForm):
	name         = StringField("Name", [InputRequired(), Length(1, 20), Regexp("^[a-z0-9_]", 0, "Lower case letters (a-z), digits (0-9), and underscores (_) only")])
	title        = StringField("Title", [InputRequired(), Length(3, 50)])
	shortDesc    = StringField("Short Description", [InputRequired(), Length(1,200)])
	desc         = TextAreaField("Long Description", [Optional(), Length(0,10000)])
	type         = SelectField("Type", [InputRequired()], choices=PackageType.choices(), coerce=PackageType.coerce, default=PackageType.MOD)
	repo         = StringField("Repo URL", [Optional(), URL()])
	website      = StringField("Website URL", [Optional(), URL()])
	issueTracker = StringField("Issue Tracker URL", [Optional(), URL()])
	forums	     = IntegerField("Forum Topic ID", [InputRequired(), NumberRange(0,999999)])
	submit	     = SubmitField("Save")

@menu.register_menu(app, ".new", "Create", order=21, visible_when=lambda: current_user.is_authenticated)
@app.route("/new/", methods=["GET", "POST"])
@app.route("/<type>s/<author>/<name>/edit/", methods=["GET", "POST"])
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

	return render_template("packages/create_edit.html", package=package, form=form)

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


class EditRequestForm(PackageForm):
	edit_title = StringField("Edit Title", [InputRequired(), Length(1, 100)])
	edit_desc  = TextField("Edit Description", [Optional()])

class UnresolvedPackage(Package):
	edit_title = ""
	edit_desc  = ""


@app.route("/<ptype>s/<author>/<name>/requests/new/", methods=["GET","POST"])
@login_required
def create_editrequest_page(ptype=None, author=None, name=None):
	package = getPageByInfo(ptype, author, name)

	form = EditRequestForm(request.form, obj=package)
	if request.method == "POST" and form.validate():
		editedPackage = UnresolvedPackage()
		form.populate_obj(editedPackage)

		erequest = EditRequest()
		erequest.package = package
		erequest.author  = current_user
		erequest.title   = editedPackage.edit_title
		erequest.desc    = editedPackage.edit_desc
		db.session.add(erequest)

		wasChangeMade = False
		for e in PackagePropertyKey:
			newValue = getattr(editedPackage, e.name)

			oldValue = getattr(package, e.name)
			if newValue == "":
				newValue = None

			newValueComp = newValue
			oldValueComp = oldValue
			if type(newValue) is str:
				newValue = newValue.replace("\r\n", "\n")
				newValueComp = newValue.strip()
				oldValueComp = oldValue.strip()

			if newValueComp != oldValueComp:
				change = EditRequestChange()
				change.request = erequest
				change.key = e
				change.oldValue = oldValue
				change.newValue = newValue
				db.session.add(change)
				wasChangeMade = True

		if wasChangeMade:
			db.session.commit()
			return redirect(package.getDetailsURL())
		else:
			flash("No changes detected", "warning")

	return render_template("packages/create_editrequest.html", package=package, form=form)


class CreatePackageReleaseForm(FlaskForm):
	name	   = StringField("Name")
	title	   = StringField("Title")
	uploadOpt  = RadioField ("File", choices=[("vcs", "From VCS Commit or Branch"), ("upload", "File Upload")])
	vcsLabel   = StringField("VCS Commit or Branch", default="master")
	fileUpload = FileField("File Upload")
	submit	   = SubmitField("Save")

class EditPackageReleaseForm(FlaskForm):
	name     = StringField("Name")
	title    = StringField("Title")
	url      = StringField("URL", [URL])
	approved = BooleanField("Is Approved")
	submit   = SubmitField("Save")

@app.route("/<type>s/<author>/<name>/releases/new/", methods=["GET", "POST"])
@login_required
def create_release_page(type, author, name):
	package = getPageByInfo(type, author, name)
	if not package.checkPerm(current_user, Permission.MAKE_RELEASE):
		return redirect(package.getDetailsURL())

	# Initial form class from post data and default data
	form = CreatePackageReleaseForm()
	if request.method == "POST" and form.validate():
		for key, value in request.files.items() :
			print (key, value)
		if form["uploadOpt"].data == "vcs":
			rel = PackageRelease()
			rel.package = package
			rel.title = form["title"].data
			rel.url = form["vcsLabel"].data
			# TODO: get URL to commit from branch name
			db.session.commit()
			return redirect(package.getDetailsURL())
		else:
			file = form.fileUpload.data
			if not file or file.filename == "":
				flash("No selected file", "error")
			elif not isFilenameAllowed(file.filename, ["zip"]):
				flash("Please select a zip file", "error")
			else:
				import random, string, os
				filename = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(10)) + ".zip"
				file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

				rel = PackageRelease()
				rel.package = package
				rel.title = form["title"].data
				rel.url = "/uploads/" + filename
				db.session.commit()
				return redirect(package.getDetailsURL())

	return render_template("packages/release_new.html", package=package, form=form)

@app.route("/<type>s/<author>/<name>/releases/<id>/", methods=["GET", "POST"])
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

	canEdit	= package.checkPerm(current_user, Permission.MAKE_RELEASE)
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

	return render_template("packages/release_edit.html", package=package, release=release, form=form)
