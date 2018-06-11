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
from flask_user import *
from app import app
from app.models import *
from app.utils import triggerNotif, clearNotifications

from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *

@app.route("/threads/")
def threads_page():
	threads = Thread.query.filter_by(private=False).all()
	return render_template("threads/list.html", threads=threads)

@app.route("/threads/<int:id>/", methods=["GET", "POST"])
def thread_page(id):
	clearNotifications(url_for("thread_page", id=id))

	thread = Thread.query.get(id)
	if thread is None or not thread.checkPerm(current_user, Permission.SEE_THREAD):
		abort(404)

	if current_user.is_authenticated and request.method == "POST":
		comment = request.form["comment"]

		if len(comment) <= 500 and len(comment) > 3:
			reply = ThreadReply()
			reply.author = current_user
			reply.comment = comment
			db.session.add(reply)

			thread.replies.append(reply)
			db.session.commit()

			return redirect(url_for("thread_page", id=id))

		else:
			flash("Comment needs to be between 3 and 500 characters.")

	return render_template("threads/view.html", thread=thread)


class ThreadForm(FlaskForm):
	title	= StringField("Title", [InputRequired(), Length(3,100)])
	comment = TextAreaField("Comment", [InputRequired(), Length(10, 500)])
	private = BooleanField("Private")
	submit  = SubmitField("Open Thread")

@app.route("/threads/new/", methods=["GET", "POST"])
@login_required
def new_thread_page():
	form = ThreadForm(formdata=request.form)

	package = None
	if "pid" in request.args:
		package = Package.query.get(int(request.args.get("pid")))
		if package is None:
			flash("Unable to find that package!", "error")

	if package is None:
		abort(403)

	def_is_private   = request.args.get("private") or False
	if not package.approved:
		def_is_private = True
	allow_change     = package.approved
	is_review_thread = package is not None and not package.approved

	# Check that user can make the thread
	if is_review_thread and not (package.author == current_user or \
			package.checkPerm(current_user, Permission.APPROVE_NEW)):
		flash("Unable to create thread!", "error")
		return redirect(url_for("home_page"))

	# Only allow creating one thread when not approved
	elif is_review_thread and package.review_thread is not None:
		flash("A review thread already exists!", "error")
		if request.method == "GET":
			return redirect(url_for("thread_page", id=package.review_thread.id))

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

		reply = ThreadReply()
		reply.thread  = thread
		reply.author  = current_user
		reply.comment = form.comment.data
		db.session.add(reply)

		thread.replies.append(reply)

		db.session.commit()

		if is_review_thread:
			package.review_thread = thread

		if package is not None:
			triggerNotif(package.author, current_user,
					"New thread '{}' on package {}".format(thread.title, package.title), url_for("thread_page", id=thread.id))
			db.session.commit()

		db.session.commit()

		return redirect(url_for("thread_page", id=thread.id))


	return render_template("threads/new.html", form=form, allow_private_change=allow_change)
