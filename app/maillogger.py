import logging
from enum import Enum
from app.tasks.emails import sendEmailRaw

def _has_newline(line):
	"""Used by has_bad_header to check for \\r or \\n"""
	if line and ("\r" in line or "\n" in line):
		return True
	return False

def _is_bad_subject(subject):
	"""Copied from: flask_mail.py class Message def has_bad_headers"""
	if _has_newline(subject):
		for linenum, line in enumerate(subject.split("\r\n")):
			if not line:
				return True
			if linenum > 0 and line[0] not in "\t ":
				return True
			if _has_newline(line):
				return True
			if len(line.strip()) == 0:
				return True
	return False


class FlaskMailSubjectFormatter(logging.Formatter):
	def format(self, record):
		record.message = record.getMessage()
		if self.usesTime():
			record.asctime = self.formatTime(record, self.datefmt)
		s = self.formatMessage(record)
		return s

class FlaskMailTextFormatter(logging.Formatter):
	pass

class FlaskMailHTMLFormatter(logging.Formatter):
	pre_template = "<h1>%s</h1><pre>%s</pre>"
	def formatException(self, exc_info):
		formatted_exception = logging.Handler.formatException(self, exc_info)
		return FlaskMailHTMLFormatter.pre_template % ("Exception information", formatted_exception)
	def formatStack(self, stack_info):
		return "<pre>%s</pre>" % stack_info


# see: https://github.com/python/cpython/blob/3.6/Lib/logging/__init__.py (class Handler)

class FlaskMailHandler(logging.Handler):
	def __init__(self, mailer, subject_template, level=logging.NOTSET):
		logging.Handler.__init__(self, level)
		self.mailer = mailer
		self.send_to = mailer.app.config["MAIL_UTILS_ERROR_SEND_TO"]
		self.subject_template = subject_template
		self.html_formatter = None

	def setFormatter(self, text_fmt, html_fmt=None):
		"""
		Set the formatters for this handler. Provide at least one formatter.
		When no text_fmt is provided, no text-part is created for the email body.
		"""
		assert (text_fmt, html_fmt) != (None, None), "At least one formatter should be provided"
		if type(text_fmt)==str:
			text_fmt = FlaskMailTextFormatter(text_fmt)
		self.formatter = text_fmt
		if type(html_fmt)==str:
			html_fmt = FlaskMailHTMLFormatter(html_fmt)
		self.html_formatter = html_fmt

	def getSubject(self, record):
		fmt = FlaskMailSubjectFormatter(self.subject_template)
		subject = fmt.format(record)
		#Since templates can cause header problems, and we rather have a incomplete email then an error, we fix this
		if _is_bad_subject(subject):
			subject="FlaskMailHandler log-entry from %s [original subject is replaced, because it would result in a bad header]" % self.mailer.app.name
		return subject

	def emit(self, record):
		record.stack_info = record.exc_text
		record.exc_text = None
		record.exc_info = None

		text = self.format(record)				if self.formatter	  else None
		html = self.html_formatter.format(record) if self.html_formatter else None
		sendEmailRaw.delay(self.send_to, self.getSubject(record), text, html)


def register_mail_error_handler(app, mailer):
	subject_template = "ContentDB %(message)s (%(module)s > %(funcName)s)"
	text_template = """
Message type: %(levelname)s
Location:	 %(pathname)s:%(lineno)d
Module:	   %(module)s
Function:	 %(funcName)s
Time:		 %(asctime)s
Message:
%(message)s"""
	html_template = """
<style>th { text-align: right}</style><table>
<tr><th>Message type:</th><td>%(levelname)s</td></tr>
<tr>	<th>Location:</th><td>%(pathname)s:%(lineno)d</td></tr>
<tr>	  <th>Module:</th><td>%(module)s</td></tr>
<tr>	<th>Function:</th><td>%(funcName)s</td></tr>
<tr>		<th>Time:</th><td>%(asctime)s</td></tr>
</table>
<h2>%(message)s</h2>"""

	mail_handler = FlaskMailHandler(mailer, subject_template)
	mail_handler.setLevel(logging.ERROR)
	mail_handler.setFormatter(text_template, html_template)
	app.logger.addHandler(mail_handler)
