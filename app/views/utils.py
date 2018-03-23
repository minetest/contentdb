from flask import request

def isFilenameAllowed(filename, exts):
	return "." in filename and \
			filename.rsplit(".", 1)[1].lower() in exts

def shouldReturnJson():
	return "application/json" in request.accept_mimetypes and \
			not "text/html" in request.accept_mimetypes
