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

bp = Blueprint("threads", __name__)

from flask_user import *
from app.models import *
from app.utils import triggerNotif, clearNotifications

import datetime

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

	return redirect(url_for("threads.view", id=id))


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
		flash("Not subscribed to thread", "success")

	return redirect(url_for("threads.view", id=id))


@bp.route("/threads/<int:id>/", methods=["GET", "POST"])
def view(id):
	clearNotifications(url_for("threads.view", id=id))

	thread = Thread.query.get(id)
	if thread is None or not thread.checkPerm(current_user, Permission.SEE_THREAD):
		abort(404)

	if current_user.is_authenticated and request.method == "POST":
		comment = request.form["comment"]

		if not current_user.canCommentRL():
			flash("Please wait before commenting again", "danger")
			if package:
				return redirect(package.getDetailsURL())
			else:
				return redirect(url_for("homepage.home"))

		if len(comment) <= 500 and len(comment) > 3:
			reply = ThreadReply()
			reply.author = current_user
			reply.comment = comment
			db.session.add(reply)

			thread.replies.append(reply)
			if not current_user in thread.watchers:
				thread.watchers.append(current_user)

			msg = None
			if thread.package is None:
				msg = "New comment on '{}'".format(thread.title)
			else:
				msg = "New comment on '{}' on package {}".format(thread.title, thread.package.title)


			for user in thread.watchers:
				if user != current_user:
					triggerNotif(user, current_user, msg, url_for("threads.view", id=thread.id))

			db.session.commit()

			return redirect(url_for("threads.view", id=id))

		else:
			flash("Comment needs to be between 3 and 500 characters.")

	return render_template("threads/view.html", thread=thread)


class ThreadForm(FlaskForm):
	title	= StringField("Title", [InputRequired(), Length(3,100)])
	comment = TextAreaField("Comment", [InputRequired(), Length(10, 500)])
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
		return redirect(url_for("threads.view", id=package.review_thread.id))

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

		notif_msg = None
		if package is not None:
			notif_msg = "New thread '{}' on package {}".format(thread.title, package.title)
			triggerNotif(package.author, current_user, notif_msg, url_for("threads.view", id=thread.id))
		else:
			notif_msg = "New thread '{}'".format(thread.title)

		for user in User.query.filter(User.rank >= UserRank.EDITOR).all():
			triggerNotif(user, current_user, notif_msg, url_for("threads.view", id=thread.id))

		db.session.commit()

		return redirect(url_for("threads.view", id=thread.id))


	return render_template("threads/new.html", form=form, allow_private_change=allow_change, package=package)
