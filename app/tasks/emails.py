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


from flask import render_template, url_for
from flask_mail import Message
from app import mail
from app.tasks import celery

@celery.task()
def sendVerifyEmail(newEmail, token):
	print("Sending verify email!")
	msg = Message("Verify email address", recipients=[newEmail])

	msg.body = """
			This email has been sent to you because someone (hopefully you)
			has entered your email address as a user's email.

			If it wasn't you, then just delete this email.

			If this was you, then please click this link to verify the address:

			{}
		""".format(url_for('verify_email_page', token=token, _external=True))

	msg.html = render_template("emails/verify.html", token=token)
	mail.send(msg)

@celery.task()
def sendEmailRaw(to, subject, text, html):
	from flask_mail import Message
	msg = Message(subject, recipients=to)

	msg.body = text or html
	html = html or text
	msg.html = render_template("emails/base.html", subject=subject, content=html)
	mail.send(msg)
