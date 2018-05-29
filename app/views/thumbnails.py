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


from flask import *
from app import app

import glob, os
from PIL import Image

ALLOWED_RESOLUTIONS=[(332,221)]

def mkdir(path):
	if not os.path.isdir(path):
		os.mkdir(path)

@app.route("/thumbnails/<img>")
@app.route("/thumbnails/<int:w>x<int:h>/<img>")
def make_thumbnail(img, w=332, h=221):
	if not (w, h) in ALLOWED_RESOLUTIONS:
		abort(403)

	mkdir("app/public/thumbnails/")
	mkdir("app/public/thumbnails/332x221/")

	cache_filepath  = "public/thumbnails/{}x{}/{}".format(w, h, img)
	source_filepath = "public/uploads/" + img

	im = Image.open("app/" + source_filepath)
	im.thumbnail((w, h), Image.ANTIALIAS)
	im.save("app/" + cache_filepath, optimize=True)
	return send_file(cache_filepath)
