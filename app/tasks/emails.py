from flask import *
from flask_mail import Message
from app import mail
from app.tasks import celery

@celery.task()
def sendVerifyEmail(newEmail, token):
    msg = Message("Verify email address", recipients=[newEmail])
    msg.body = "This is a verification email!"
    msg.html = render_template("emails/verify.html", token=token)
    mail.send(msg)
