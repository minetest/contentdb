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


from flask import render_template
from flask_mail import Message
from app import mail
from app.models import Notification, db, EmailSubscription, User
from app.tasks import celery
from app.utils import abs_url_for, abs_url, randomString


def get_email_subscription(email):
	assert type(email) == str
	ret = EmailSubscription.query.filter_by(email=email).first()
	if not ret:
		ret = EmailSubscription(email)
		ret.token = randomString(32)
		db.session.add(ret)
		db.session.commit()

	return ret


@celery.task()
def send_verify_email(email, token):
	sub = get_email_subscription(email)
	if sub.blacklisted:
		return

	msg = Message("Confirm email address", recipients=[email])

	msg.body = """
			This email has been sent to you because someone (hopefully you)
			has entered your email address as a user's email.

			If it wasn't you, then just delete this email.

			If this was you, then please click this link to confirm the address:

			{}
		""".format(abs_url_for('users.verify_email', token=token))

	msg.html = render_template("emails/verify.html", token=token, sub=sub)
	mail.send(msg)


@celery.task()
def send_unsubscribe_verify(email):
	sub = get_email_subscription(email)
	if sub.blacklisted:
		return

	msg = Message("Confirm unsubscribe", recipients=[email])

	msg.body = """
				We're sorry to see you go. You just need to do one more thing before your email is blacklisted.
				
				Click this link to blacklist email: {} 
			""".format(abs_url_for('users.unsubscribe', token=sub.token))

	msg.html = render_template("emails/verify_unsubscribe.html", sub=sub)
	mail.send(msg)


@celery.task()
def send_email_with_reason(email, subject, text, html, reason):
	sub = get_email_subscription(email)
	if sub.blacklisted:
		return

	from flask_mail import Message
	msg = Message(subject, recipients=[email])

	msg.body = text
	html = html or text
	msg.html = render_template("emails/base.html", subject=subject, content=html, reason=reason, sub=sub)
	mail.send(msg)


@celery.task()
def send_user_email(email: str, subject: str, text: str, html=None):
	return send_email_with_reason(email, subject, text, html,
			"You are receiving this email because you are a registered user of ContentDB.")


@celery.task()
def send_anon_email(email: str, subject: str, text: str, html=None):
	return send_email_with_reason(email, subject, text, html,
			"You are receiving this email because someone (hopefully you) entered your email address as a user's email.")


def send_single_email(notification):
	sub = get_email_subscription(notification.user.email)
	if sub.blacklisted:
		return

	msg = Message(notification.title, recipients=[notification.user.email])

	msg.body = """
			New notification: {}
			
			View: {}
			
			Manage email settings: {}
			Unsubscribe: {}
		""".format(notification.title, abs_url(notification.url),
					abs_url_for("users.email_notifications", username=notification.user.username),
					abs_url_for("users.unsubscribe", token=sub.token))

	msg.html = render_template("emails/notification.html", notification=notification, sub=sub)
	mail.send(msg)


def send_notification_digest(notifications: [Notification]):
	user = notifications[0].user

	sub = get_email_subscription(user.email)
	if sub.blacklisted:
		return

	msg = Message("{} new notifications".format(len(notifications)), recipients=[user.email])

	msg.body = "".join(["<{}> {}\nView: {}\n\n".format(notification.causer.display_name, notification.title, abs_url(notification.url)) for notification in notifications])

	msg.body += "Manage email settings: {}\nUnsubscribe: {}".format(
			abs_url_for("users.email_notifications", username=user.username),
			abs_url_for("users.unsubscribe", token=sub.token))

	msg.html = render_template("emails/notification_digest.html", notifications=notifications, user=user, sub=sub)
	mail.send(msg)


@celery.task()
def send_pending_digests():
	for user in User.query.filter(User.notifications.any(emailed=False)).all():
		to_send = []
		for notification in user.notifications:
			if not notification.emailed and notification.can_send_digest():
				to_send.append(notification)
				notification.emailed = True

		if len(to_send) > 0:
			send_notification_digest(to_send)

		db.session.commit()


@celery.task()
def send_pending_notifications():
	for user in User.query.filter(User.notifications.any(emailed=False)).all():
		to_send = []
		for notification in user.notifications:
			if not notification.emailed:
				if notification.can_send_email():
					to_send.append(notification)
					notification.emailed = True
				elif not notification.can_send_digest():
					notification.emailed = True

		db.session.commit()

		if len(to_send) > 1:
			send_notification_digest(to_send)
		elif len(to_send) > 0:
			send_single_email(to_send[0])
