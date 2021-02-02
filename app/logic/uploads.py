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

from app.logic.LogicError import LogicError
from app.models import *
from app.utils import randomString


def get_extension(filename):
	return filename.rsplit(".", 1)[1].lower() if "." in filename else None

ALLOWED_IMAGES = {"jpeg", "png"}
def isAllowedImage(data):
	return imghdr.what(None, data) in ALLOWED_IMAGES

def upload_file(file, fileType, fileTypeDesc):
	if not file or file is None or file.filename == "":
		raise LogicError(400, "Expected file")

	assert os.path.isdir(app.config["UPLOAD_DIR"]), "UPLOAD_DIR must exist"

	isImage = False
	if fileType == "image":
		allowedExtensions = ["jpg", "jpeg", "png"]
		isImage = True
	elif fileType == "zip":
		allowedExtensions = ["zip"]
	else:
		raise Exception("Invalid fileType")

	ext = get_extension(file.filename)
	if ext is None or not ext in allowedExtensions:
		raise LogicError(400, "Please upload " + fileTypeDesc)

	if isImage and not isAllowedImage(file.stream.read()):
		raise LogicError(400, "Uploaded image isn't actually an image")

	file.stream.seek(0)

	filename = randomString(10) + "." + ext
	filepath = os.path.join(app.config["UPLOAD_DIR"], filename)
	file.save(filepath)

	return "/uploads/" + filename, filepath
