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
from flask import *
from flask_babel import gettext, lazy_gettext

from app.markdown import get_user_mentions, render_markdown
from app.tasks.webhooktasks import post_discord_webhook

bp = Blueprint("threads", __name__)

from flask_login import current_user, login_required
from app.models import *
from app.utils import addNotification, isYes, addAuditLog, get_system_user, rank_required
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from app.utils import get_int_or_abort


@bp.route("/threads/")
def list_all():
	query = Thread.query
	if not Permission.SEE_THREAD.check(current_user):
		query = query.filter_by(private=False)

	package = None
	pid = request.args.get("pid")
	if pid:
		pid = get_int_or_abort(pid)
		package = Package.query.get(pid)
		query = query.filter_by(package=package)

	query = query.filter_by(review_id=None)

	query = query.order_by(db.desc(Thread.created_at))

	page = get_int_or_abort(request.args.get("page"), 1)
	num = min(40, get_int_or_abort(request.args.get("n"), 100))

	pagination = query.paginate(page, num, True)

	return render_template("threads/list.html", pagination=pagination, threads=pagination.items, package=package)


@bp.route("/threads/<int:id>/subscribe/", methods=["POST"])
@login_required
def subscribe(id):
	thread = Thread.query.get(id)
	if thread is None or not thread.checkPerm(current_user, Permission.SEE_THREAD):
		abort(404)

	if current_user in thread.watchers:
		flash(gettext("Already subscribed!"), "success")
	else:
		flash(gettext("Subscribed to thread"), "success")
		thread.watchers.append(current_user)
		db.session.commit()

	return redirect(thread.getViewURL())


@bp.route("/threads/<int:id>/unsubscribe/", methods=["POST"])
@login_required
def unsubscribe(id):
	thread = Thread.query.get(id)
	if thread is None or not thread.checkPerm(current_user, Permission.SEE_THREAD):
		abort(404)

	if current_user in thread.watchers:
		flash(gettext("Unsubscribed!"), "success")
		thread.watchers.remove(current_user)
		db.session.commit()
	else:
		flash(gettext("Already not subscribed!"), "success")

	return redirect(thread.getViewURL())


@bp.route("/threads/<int:id>/set-lock/", methods=["POST"])
@login_required
def set_lock(id):
	thread = Thread.query.get(id)
	if thread is None or not thread.checkPerm(current_user, Permission.LOCK_THREAD):
		abort(404)

	thread.locked = isYes(request.args.get("lock"))
	if thread.locked is None:
		abort(400)

	msg = None
	if thread.locked:
		msg = "Locked thread '{}'".format(thread.title)
		flash(gettext("Locked thread"), "success")
	else:
		msg = "Unlocked thread '{}'".format(thread.title)
		flash(gettext("Unlocked thread"), "success")

	addNotification(thread.watchers, current_user, NotificationType.OTHER, msg, thread.getViewURL(), thread.package)
	addAuditLog(AuditSeverity.MODERATION, current_user, msg, thread.getViewURL(), thread.package)

	db.session.commit()

	return redirect(thread.getViewURL())


@bp.route("/threads/<int:id>/delete/", methods=["GET", "POST"])
@login_required
def delete_thread(id):
	thread = Thread.query.get(id)
	if thread is None or not thread.checkPerm(current_user, Permission.DELETE_THREAD):
		abort(404)

	if request.method == "GET":
		return render_template("threads/delete_thread.html", thread=thread)

	summary = "\n\n".join([("<{}> {}".format(reply.author.display_name, reply.comment)) for reply in thread.replies])

	msg = "Deleted thread {} by {}".format(thread.title, thread.author.display_name)

	db.session.delete(thread)

	addAuditLog(AuditSeverity.MODERATION, current_user, msg, None, thread.package, summary)

	db.session.commit()

	return redirect(url_for("homepage.home"))


@bp.route("/threads/<int:id>/delete-reply/", methods=["GET", "POST"])
@login_required
def delete_reply(id):
	thread = Thread.query.get(id)
	if thread is None:
		abort(404)

	reply_id = request.args.get("reply")
	if reply_id is None:
		abort(404)

	reply = ThreadReply.query.get(reply_id)
	if reply is None or reply.thread != thread:
		abort(404)

	if thread.first_reply == reply:
		flash(gettext("Cannot delete thread opening post!"), "danger")
		return redirect(thread.getViewURL())

	if not reply.checkPerm(current_user, Permission.DELETE_REPLY):
		abort(403)

	if request.method == "GET":
		return render_template("threads/delete_reply.html", thread=thread, reply=reply)

	msg = "Deleted reply by {}".format(reply.author.display_name)
	addAuditLog(AuditSeverity.MODERATION, current_user, msg, thread.getViewURL(), thread.package, reply.comment)

	db.session.delete(reply)
	db.session.commit()

	return redirect(thread.getViewURL())


class CommentForm(FlaskForm):
	comment = TextAreaField(lazy_gettext("Comment"), [InputRequired(), Length(10, 2000)])
	submit  = SubmitField(lazy_gettext("Comment"))


@bp.route("/threads/<int:id>/edit/", methods=["GET", "POST"])
@login_required
def edit_reply(id):
	thread = Thread.query.get(id)
	if thread is None:
		abort(404)

	reply_id = request.args.get("reply")
	if reply_id is None:
		abort(404)

	reply = ThreadReply.query.get(reply_id)
	if reply is None or reply.thread != thread:
		abort(404)

	if not reply.checkPerm(current_user, Permission.EDIT_REPLY):
		abort(403)

	form = CommentForm(formdata=request.form, obj=reply)
	if form.validate_on_submit():
		comment = form.comment.data

		msg = "Edited reply by {}".format(reply.author.display_name)
		severity = AuditSeverity.NORMAL if current_user == reply.author else AuditSeverity.MODERATION
		addNotification(reply.author, current_user, NotificationType.OTHER, msg, thread.getViewURL(), thread.package)
		addAuditLog(severity, current_user, msg, thread.getViewURL(), thread.package, reply.comment)

		reply.comment = comment

		db.session.commit()

		return redirect(thread.getViewURL())

	return render_template("threads/edit_reply.html", thread=thread, reply=reply, form=form)


@bp.route("/threads/<int:id>/", methods=["GET", "POST"])
def view(id):
	thread: Thread = Thread.query.get(id)
	if thread is None or not thread.checkPerm(current_user, Permission.SEE_THREAD):
		abort(404)

	form = CommentForm(formdata=request.form) if thread.checkPerm(current_user, Permission.COMMENT_THREAD) else None

	# Check that title is none to load comments into textarea if redirected from new thread page
	if form and form.validate_on_submit() and request.form.get("title") is None:
		comment = form.comment.data

		if not current_user.canCommentRL():
			flash(gettext("Please wait before commenting again"), "danger")
			return redirect(thread.getViewURL())

		reply = ThreadReply()
		reply.author = current_user
		reply.comment = comment
		db.session.add(reply)

		thread.replies.append(reply)
		if current_user not in thread.watchers:
			thread.watchers.append(current_user)

		for mentioned_username in get_user_mentions(render_markdown(comment)):
			mentioned = User.query.filter_by(username=mentioned_username).first()
			if mentioned is None:
				continue

			msg = "Mentioned by {} in '{}'".format(current_user.display_name, thread.title)
			addNotification(mentioned, current_user, NotificationType.THREAD_REPLY,
					msg, thread.getViewURL(), thread.package)

			thread.watchers.append(mentioned)

		msg = "New comment on '{}'".format(thread.title)
		addNotification(thread.watchers, current_user, NotificationType.THREAD_REPLY, msg, thread.getViewURL(), thread.package)

		if thread.author == get_system_user():
			approvers = User.query.filter(User.rank >= UserRank.APPROVER).all()
			addNotification(approvers, current_user, NotificationType.EDITOR_MISC, msg,
					thread.getViewURL(), thread.package)
			post_discord_webhook.delay(current_user.username,
					"Replied to bot messages: {}".format(thread.getViewURL(absolute=True)), True)

		db.session.commit()

		return redirect(thread.getViewURL())

	return render_template("threads/view.html", thread=thread, form=form)


class ThreadForm(FlaskForm):
	title	= StringField(lazy_gettext("Title"), [InputRequired(), Length(3,100)])
	comment = TextAreaField(lazy_gettext("Comment"), [InputRequired(), Length(10, 2000)])
	private = BooleanField(lazy_gettext("Private"))
	submit  = SubmitField(lazy_gettext("Open Thread"))


@bp.route("/threads/new/", methods=["GET", "POST"])
@login_required
def new():
	form = ThreadForm(formdata=request.form)

	package = None
	if "pid" in request.args:
		package = Package.query.get(int(request.args.get("pid")))
		if package is None:
			abort(404)

	def_is_private = request.args.get("private") or False
	if package is None and not current_user.rank.atLeast(UserRank.APPROVER):
		abort(404)

	allow_private_change = not package or package.approved
	is_review_thread = package and not package.approved

	# Check that user can make the thread
	if package and not package.checkPerm(current_user, Permission.CREATE_THREAD):
		flash(gettext("Unable to create thread!"), "danger")
		return redirect(url_for("homepage.home"))

	# Only allow creating one thread when not approved
	elif is_review_thread and package.review_thread is not None:
		# Redirect submit to `view` page, which checks for `title` in the form data and so won't commit the reply
		flash(gettext("An approval thread already exists! Consider replying there instead"), "danger")
		return redirect(package.review_thread.getViewURL(), code=307)

	elif not current_user.canOpenThreadRL():
		flash(gettext("Please wait before opening another thread"), "danger")

		if package:
			return redirect(package.getURL("packages.view"))
		else:
			return redirect(url_for("homepage.home"))

	# Set default values
	elif request.method == "GET":
		form.private.data = def_is_private
		form.title.data   = request.args.get("title") or ""

	# Validate and submit
	elif form.validate_on_submit():
		thread = Thread()
		thread.author  = current_user
		thread.title   = form.title.data
		thread.private = form.private.data if allow_private_change else def_is_private
		thread.package = package
		db.session.add(thread)

		thread.watchers.append(current_user)
		if package and package.author != current_user:
			thread.watchers.append(package.author)

		reply = ThreadReply()
		reply.thread  = thread
		reply.author  = current_user
		reply.comment = form.comment.data
		db.session.add(reply)

		thread.replies.append(reply)

		db.session.commit()

		if is_review_thread:
			package.review_thread = thread

		for mentioned_username in get_user_mentions(render_markdown(form.comment.data)):
			mentioned = User.query.filter_by(username=mentioned_username).first()
			if mentioned is None:
				continue

			msg = "Mentioned by {} in new thread '{}'".format(current_user.display_name, thread.title)
			addNotification(mentioned, current_user, NotificationType.NEW_THREAD,
							msg, thread.getViewURL(), thread.package)

			thread.watchers.append(mentioned)

		notif_msg = "New thread '{}'".format(thread.title)
		if package is not None:
			addNotification(package.maintainers, current_user, NotificationType.NEW_THREAD, notif_msg, thread.getViewURL(), package)

		approvers = User.query.filter(User.rank >= UserRank.APPROVER).all()
		addNotification(approvers, current_user, NotificationType.EDITOR_MISC, notif_msg, thread.getViewURL(), package)

		if is_review_thread:
			post_discord_webhook.delay(current_user.username,
					"Opened approval thread: {}".format(thread.getViewURL(absolute=True)), True)

		db.session.commit()

		return redirect(thread.getViewURL())


	return render_template("threads/new.html", form=form, allow_private_change=allow_private_change, package=package)


@bp.route("/users/<username>/comments/")
@rank_required(UserRank.EDITOR)
def user_comments(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)

	return render_template("threads/user_comments.html", user=user, replies=user.replies)
