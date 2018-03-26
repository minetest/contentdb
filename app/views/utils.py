from flask import request, flash
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
