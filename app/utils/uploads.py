# ContentDB
# Copyright (C) 2018-21 rubenwardy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import imghdr
import os
import random
import string

from flask import request, flash

from app.models import *


def getExtension(filename):
	return filename.rsplit(".", 1)[1].lower() if "." in filename else None

ALLOWED_IMAGES = {"jpeg", "png"}
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
		flash("Please upload " + fileTypeDesc, "danger")
		return None, None

	if isImage and not isAllowedImage(file.stream.read()):
		flash("Uploaded image isn't actually an image", "danger")
		return None, None

	file.stream.seek(0)

	filename = randomString(10) + "." + ext
	filepath = os.path.join(app.config["UPLOAD_DIR"], filename)
	file.save(filepath)
	return "/uploads/" + filename, filepath
