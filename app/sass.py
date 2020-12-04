# -*- coding: utf-8 -*-
"""
A small Flask extension that makes it easy to use Sass (SCSS) with your
Flask application.

Code unabashedly adapted from https://github.com/weapp/flask-coffee2js

:copyright: (c) 2012 by Ivan Miric.
:license: MIT, see LICENSE for more details.
"""

import os
import os.path
import codecs
from flask import *
from scss import Scss

def _convert(dir, src, dst):
	original_wd = os.getcwd()
	os.chdir(dir)

	css = Scss()
	source = codecs.open(src, 'r', encoding='utf-8').read()
	output = css.compile(source)

	os.chdir(original_wd)

	outfile = codecs.open(dst, 'w', encoding='utf-8')
	outfile.write(output)
	outfile.close()

def _getDirPath(app, originalPath, create=False):
	path = originalPath

	if not os.path.isdir(path):
		path = os.path.join(app.root_path, path)

	if not os.path.isdir(path):
		if create:
			os.mkdir(path)
		else:
			raise IOError("Unable to find " + originalPath)

	return path

def sass(app, inputDir='scss', outputPath='static', force=False, cacheDir="public/static"):
	static_url_path = app.static_url_path
	inputDir = _getDirPath(app, inputDir)
	cacheDir = _getDirPath(app, cacheDir or outputPath, True)

	def _sass(filepath):
		sassfile = "%s/%s.scss" % (inputDir, filepath)
		cacheFile = "%s/%s.css" % (cacheDir, filepath)

		# Source file exists, and needs regenerating
		if os.path.isfile(sassfile) and (force or not os.path.isfile(cacheFile) or
										 os.path.getmtime(sassfile) > os.path.getmtime(cacheFile)):
			_convert(inputDir, sassfile, cacheFile)
			app.logger.debug('Compiled %s into %s' % (sassfile, cacheFile))

		return send_from_directory(cacheDir, filepath + ".css")

	app.add_url_rule("/%s/<path:filepath>.css" % outputPath, 'sass', _sass)
