# ContentDB
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


from flask import render_template
from flask_mail import Message
from app import mail
from app.models import Notification, db
from app.tasks import celery
from app.utils import abs_url_for, abs_url


@celery.task()
def sendVerifyEmail(newEmail, token):
	msg = Message("Confirm email address", recipients=[newEmail])

	msg.body = """
			This email has been sent to you because someone (hopefully you)
			has entered your email address as a user's email.

			If it wasn't you, then just delete this email.

			If this was you, then please click this link to confirm the address:

			{}
		""".format(abs_url_for('users.verify_email', token=token))

	msg.html = render_template("emails/verify.html", token=token)
	mail.send(msg)


@celery.task()
def send_email_with_reason(to, subject, text, html, reason):
	from flask_mail import Message
	msg = Message(subject, recipients=to)

	msg.body = text
	html = html or text
	msg.html = render_template("emails/base.html", subject=subject, content=html, reason=reason)
	mail.send(msg)


@celery.task()
def send_user_email(to, subject, text, html=None):
	return send_email_with_reason(to, subject, text, html,
			"You are receiving this email because you are a registered user of ContentDB.")


@celery.task()
def send_anon_email(to, subject, text, html=None):
	return send_email_with_reason(to, subject, text, html,
			"You are receiving this email because someone (hopefully you) entered your email address as a user's email.")


def sendNotificationEmail(notification):
	msg = Message(notification.title, recipients=[notification.user.email])

	msg.body = """
			New notification: {}
			
			View: {}
			
			Manage email settings: {}
		""".format(notification.title, abs_url(notification.url),
					abs_url_for("users.email_notifications", username=notification.user.username))

	msg.html = render_template("emails/notification.html", notification=notification)
	mail.send(msg)


@celery.task()
def sendPendingNotifications():
	for notification in Notification.query.filter_by(emailed=False).all():
		if notification.can_send_email():
			sendNotificationEmail(notification)

		notification.emailed = True
		db.session.commit()
