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


from flask import *

bp = Blueprint("threads", __name__)

from flask_login import current_user, login_required
from app.models import *
from app.utils import addNotification, isYes, addAuditLog

from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from app.utils import get_int_or_abort

@bp.route("/threads/")
def list_all():
	query = Thread.query
	if not Permission.SEE_THREAD.check(current_user):
		query = query.filter_by(private=False)

	pid = request.args.get("pid")
	if pid:
		pid = get_int_or_abort(pid)
		query = query.filter_by(package_id=pid)

	query = query.order_by(db.desc(Thread.created_at))

	return render_template("threads/list.html", threads=query.all())


@bp.route("/threads/<int:id>/subscribe/", methods=["POST"])
@login_required
def subscribe(id):
	thread = Thread.query.get(id)
	if thread is None or not thread.checkPerm(current_user, Permission.SEE_THREAD):
		abort(404)

	if current_user in thread.watchers:
		flash("Already subscribed!", "success")
	else:
		flash("Subscribed to thread", "success")
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
		flash("Unsubscribed!", "success")
		thread.watchers.remove(current_user)
		db.session.commit()
	else:
		flash("Already not subscribed!", "success")

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
		flash("Locked thread", "success")
	else:
		msg = "Unlocked thread '{}'".format(thread.title)
		flash("Unlocked thread", "success")

	addNotification(thread.watchers, current_user, msg, thread.getViewURL(), thread.package)
	addAuditLog(AuditSeverity.MODERATION, current_user, msg, thread.getViewURL(), thread.package)

	db.session.commit()

	return redirect(thread.getViewURL())


@bp.route("/threads/<int:id>/delete/", methods=["GET", "POST"])
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

	if thread.replies[0] == reply:
		flash("Cannot delete thread opening post!", "danger")
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
	comment = TextAreaField("Comment", [InputRequired(), Length(10, 2000)])
	submit  = SubmitField("Comment")


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
	if request.method == "POST" and form.validate():
		comment = form.comment.data

		msg = "Edited reply by {}".format(reply.author.display_name)
		severity = AuditSeverity.NORMAL if current_user == reply.author else AuditSeverity.MODERATION
		addNotification(reply.author, current_user, msg, thread.getViewURL(), thread.package)
		addAuditLog(severity, current_user, msg, thread.getViewURL(), thread.package, reply.comment)

		reply.comment = comment

		db.session.commit()

		return redirect(thread.getViewURL())

	return render_template("threads/edit_reply.html", thread=thread, reply=reply, form=form)


@bp.route("/threads/<int:id>/", methods=["GET", "POST"])
def view(id):
	thread = Thread.query.get(id)
	if thread is None or not thread.checkPerm(current_user, Permission.SEE_THREAD):
		abort(404)

	if current_user.is_authenticated and request.method == "POST":
		comment = request.form["comment"]

		if not thread.checkPerm(current_user, Permission.COMMENT_THREAD):
			flash("You cannot comment on this thread", "danger")
			return redirect(thread.getViewURL())

		if not current_user.canCommentRL():
			flash("Please wait before commenting again", "danger")
			return redirect(thread.getViewURL())

		if 2000 >= len(comment) > 3:
			reply = ThreadReply()
			reply.author = current_user
			reply.comment = comment
			db.session.add(reply)

			thread.replies.append(reply)
			if not current_user in thread.watchers:
				thread.watchers.append(current_user)

			msg = "New comment on '{}'".format(thread.title)
			addNotification(thread.watchers, current_user, msg, thread.getViewURL(), thread.package)
			db.session.commit()

			return redirect(thread.getViewURL())

		else:
			flash("Comment needs to be between 3 and 2000 characters.")

	return render_template("threads/view.html", thread=thread)


class ThreadForm(FlaskForm):
	title	= StringField("Title", [InputRequired(), Length(3,100)])
	comment = TextAreaField("Comment", [InputRequired(), Length(10, 2000)])
	private = BooleanField("Private")
	submit  = SubmitField("Open Thread")


@bp.route("/threads/new/", methods=["GET", "POST"])
@login_required
def new():
	form = ThreadForm(formdata=request.form)

	package = None
	if "pid" in request.args:
		package = Package.query.get(int(request.args.get("pid")))
		if package is None:
			flash("Unable to find that package!", "danger")

	# Don't allow making orphan threads on approved packages for now
	if package is None:
		abort(403)

	def_is_private   = request.args.get("private") or False
	if package is None:
		def_is_private = True
	allow_change     = package and package.approved
	is_review_thread = package and not package.approved

	# Check that user can make the thread
	if not package.checkPerm(current_user, Permission.CREATE_THREAD):
		flash("Unable to create thread!", "danger")
		return redirect(url_for("homepage.home"))

	# Only allow creating one thread when not approved
	elif is_review_thread and package.review_thread is not None:
		flash("A review thread already exists!", "danger")
		return redirect(package.review_thread.getViewURL())

	elif not current_user.canOpenThreadRL():
		flash("Please wait before opening another thread", "danger")

		if package:
			return redirect(package.getDetailsURL())
		else:
			return redirect(url_for("homepage.home"))

	# Set default values
	elif request.method == "GET":
		form.private.data = def_is_private
		form.title.data   = request.args.get("title") or ""

	# Validate and submit
	elif request.method == "POST" and form.validate():
		thread = Thread()
		thread.author  = current_user
		thread.title   = form.title.data
		thread.private = form.private.data if allow_change else def_is_private
		thread.package = package
		db.session.add(thread)

		thread.watchers.append(current_user)
		if package is not None and package.author != current_user:
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

			if package.state == PackageState.READY_FOR_REVIEW and current_user not in package.maintainers:
				package.state = PackageState.CHANGES_NEEDED


		notif_msg = "New thread '{}'".format(thread.title)
		if package is not None:
			addNotification(package.maintainers, current_user, notif_msg, thread.getViewURL(), package)

		editors = User.query.filter(User.rank >= UserRank.EDITOR).all()
		addNotification(editors, current_user, notif_msg, thread.getViewURL(), package)

		db.session.commit()

		return redirect(thread.getViewURL())


	return render_template("threads/new.html", form=form, allow_private_change=allow_change, package=package)
