# Content DB
# Copyright (C) 2018  rubenwardy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from flask import request, flash, abort, redirect
from flask_user import *
from flask_login import login_user, logout_user
from app.models import *
from app import app
import random, string, os, imghdr

def get_int_or_abort(v, default=None):
	try:
		return int(v or default)
	except ValueError:
		abort(400)

def getExtension(filename):
	return filename.rsplit(".", 1)[1].lower() if "." in filename else None

def isFilenameAllowed(filename, exts):
	return getExtension(filename) in exts

ALLOWED_IMAGES = set(["jpeg", "png"])
def isAllowedImage(data):
	return imghdr.what(None, data) in ALLOWED_IMAGES

def shouldReturnJson():
	return "application/json" in request.accept_mimetypes and \
			not "text/html" in request.accept_mimetypes

def randomString(n):
	return ''.join(random.choice(string.ascii_lowercase + \
			string.ascii_uppercase + string.digits) for _ in range(n))

def doFileUpload(file, fileType, fileTypeDesc):
	if not file or file is None or file.filename == "":
		flash("No selected file", "danger")
		return None, None

	assert os.path.isdir(app.config["UPLOAD_DIR"]), "UPLOAD_DIR must exist"

	allowedExtensions = []
	isImage = False
	if fileType == "image":
		allowedExtensions = ["jpg", "jpeg", "png"]
		isImage = True
	elif fileType == "zip":
		allowedExtensions = ["zip"]
	else:
		raise Exception("Invalid fileType")

	ext = getExtension(file.filename)
	if ext is None or not ext in allowedExtensions:
		flash("Please upload load " + fileTypeDesc, "danger")
		return None, None

	if isImage and not isAllowedImage(file.stream.read()):
		flash("Uploaded image isn't actually an image", "danger")
		return None, None

	file.stream.seek(0)

	filename = randomString(10) + "." + ext
	filepath = os.path.join(app.config["UPLOAD_DIR"], filename)
	file.save(filepath)
	return "/uploads/" + filename, filepath

def make_flask_user_password(plaintext_str):
	# http://passlib.readthedocs.io/en/stable/modular_crypt_format.html
	# http://passlib.readthedocs.io/en/stable/lib/passlib.hash.bcrypt.html#format-algorithm
	# Flask_User stores passwords in the Modular Crypt Format.
	# https://github.com/lingthio/Flask-User/blob/master/flask_user/user_manager__settings.py#L166
	#   Note that Flask_User allows customizing password algorithms.
	#   USER_PASSLIB_CRYPTCONTEXT_SCHEMES defaults to bcrypt but if
	#   default changes or is customized, the code below needs adapting.
	# Individual password values will look like:
	#   $2b$12$.az4S999Ztvy/wa3UdQvMOpcki1Qn6VYPXmEFMIdWQyYs7ULnH.JW
	#   $XX$RR$SSSSSSSSSSSSSSSSSSSSSSHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
	# $XX : Selects algorithm (2b is bcrypt).
	# $RR : Selects bcrypt key expansion rounds (12 is 2**12 rounds).
	# $SSS... : 22 chars of (random, per-password) salt
	#  HHH... : 31 remaining chars of password hash (note no dollar sign)
	import bcrypt
	plaintext = plaintext_str.encode("UTF-8")
	password = bcrypt.hashpw(plaintext, bcrypt.gensalt())
	if isinstance(password, str):
		return password
	else:
		return password.decode("UTF-8")

def loginUser(user):
	def _call_or_get(v):
		if callable(v):
			return v()
		else:
			return v

	# User must have been authenticated
	if not user:
		return False

	if user.rank == UserRank.BANNED:
		flash("You have been banned.", "danger")
		return False

	user.active = True
	if not user.rank.atLeast(UserRank.NEW_MEMBER):
		user.rank = UserRank.MEMBER

	db.session.commit()

	# Check if user account has been disabled
	if not _call_or_get(user.is_active):
		flash("Your account has not been enabled.", "danger")
		return False

	# Use Flask-Login to sign in user
	login_user(user, remember=True)
	signals.user_logged_in.send(current_app._get_current_object(), user=user)

	flash("You have signed in successfully.", "success")

	return True


def rank_required(rank):
	def decorator(f):
		@wraps(f)
		def decorated_function(*args, **kwargs):
			if not current_user.is_authenticated:
				return redirect(url_for("user.login"))
			if not current_user.rank.atLeast(rank):
				abort(403)

			return f(*args, **kwargs)

		return decorated_function
	return decorator

def getPackageByInfo(author, name):
	user = User.query.filter_by(username=author).first()
	if user is None:
		abort(404)

	package = Package.query.filter_by(name=name, author_id=user.id, soft_deleted=False).first()
	if package is None:
		abort(404)

	return package

def is_package_page(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if not ("author" in kwargs and "name" in kwargs):
			abort(400)

		package = getPackageByInfo(kwargs["author"], kwargs["name"])

		del kwargs["author"]
		del kwargs["name"]

		return f(package=package, *args, **kwargs)

	return decorated_function

def triggerNotif(owner, causer, title, url):
	if owner.rank.atLeast(UserRank.NEW_MEMBER) and owner != causer:
		Notification.query.filter_by(user=owner, url=url).delete()
		notif = Notification(owner, causer, title, url)
		db.session.add(notif)

def clearNotifications(url):
	if current_user.is_authenticated:
		Notification.query.filter_by(user=current_user, url=url).delete()
		db.session.commit()


YESES = ["yes", "true", "1", "on"]

def isYes(val):
	return val and val.lower() in YESES


def isNo(val):
	return val and not isYes(val)
