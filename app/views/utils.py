from flask import request, flash, abort
from flask_user import *
from flask_login import login_user, logout_user
from app.models import *
from app import app
import random, string, os

def getExtension(filename):
	return filename.rsplit(".", 1)[1].lower() if "." in filename else None

def isFilenameAllowed(filename, exts):
	return getExtension(filename) in exts

def shouldReturnJson():
	return "application/json" in request.accept_mimetypes and \
			not "text/html" in request.accept_mimetypes

def randomString(n):
	return ''.join(random.choice(string.ascii_lowercase + \
			string.ascii_uppercase + string.digits) for _ in range(n))

def doFileUpload(file, allowedExtensions, fileTypeName):
	if not file or file is None or file.filename == "":
		flash("No selected file", "error")
		return None

	ext = getExtension(file.filename)
	if ext is None or not ext in allowedExtensions:
		flash("Please upload load " + fileTypeName, "error")
		return None

	filename = randomString(10) + "." + ext
	file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
	return "/uploads/" + filename


def _do_login_user(user, remember_me=False):
	def _call_or_get(v):
		if callable(v):
			return v()
		else:
			return v

	# User must have been authenticated
	if not user:
		return False

	user.active = True
	if not user.rank.atLeast(UserRank.NEW_MEMBER):
		user.rank = UserRank.NEW_MEMBER

	db.session.commit()

	# Check if user account has been disabled
	if not _call_or_get(user.is_active):
		flash("Your account has not been enabled.", "error")
		return False

	# Check if user has a confirmed email address
	user_manager = current_app.user_manager
	if user_manager.enable_email and user_manager.enable_confirm_email \
			and not current_app.user_manager.enable_login_without_confirm_email \
			and not user.has_confirmed_email():
		url = url_for("user.resend_confirm_email")
		flash("Your email address has not yet been confirmed", "error")
		return False

	# Use Flask-Login to sign in user
	login_user(user, remember=remember_me)
	signals.user_logged_in.send(current_app._get_current_object(), user=user)

	flash("You have signed in successfully.", "success")

	return True

def loginUser(user):
	user_mixin = None
	if user_manager.enable_username:
		user_mixin = user_manager.find_user_by_username(user.username)

	return _do_login_user(user_mixin, False)

def rank_required(rank):
	def decorator(f):
		@wraps(f)
		def decorated_function(*args, **kwargs):
			if not current_user.rank.atLeast(rank):
				abort(403)

			return f(*args, **kwargs)

		return decorated_function
	return decorator
