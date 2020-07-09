# Content DB
# Copyright (C) 2020  rubenwardy
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

from . import bp

from flask import *
from flask_user import *
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from app.models import db, PackageReview, Thread, ThreadReply
from app.utils import is_package_page, addNotification

class ReviewForm(FlaskForm):
	title	= StringField("Title", [InputRequired(), Length(3,100)])
	comment = TextAreaField("Comment", [InputRequired(), Length(10, 500)])
	recommends = RadioField("Private", [InputRequired()], choices=[("yes", "Yes"), ("no", "No")])
	submit  = SubmitField("Save")

@bp.route("/packages/<author>/<name>/review/", methods=["GET", "POST"])
@login_required
@is_package_page
def review(package):
	review = PackageReview.query.filter_by(package=package, author=current_user).first()

	form = ReviewForm(formdata=request.form, obj=review)

	# Set default values
	if request.method == "GET" and review:
		form.title.data = review.thread.title
		form.recommends.data = "yes" if review.recommends else "no"
		form.comment.data = review.thread.replies[0].comment

	# Validate and submit
	elif request.method == "POST" and form.validate():
		was_new = False
		if not review:
			was_new = True
			review = PackageReview()
			review.package = package
			review.author  = current_user
			db.session.add(review)

		review.recommends = form.recommends.data == "yes"

		thread = review.thread
		if not thread:
			thread = Thread()
			thread.author  = current_user
			thread.private = False
			thread.package = package
			thread.review = review
			db.session.add(thread)

			thread.watchers.append(current_user)

			reply = ThreadReply()
			reply.thread  = thread
			reply.author  = current_user
			reply.comment = form.comment.data
			db.session.add(reply)

			thread.replies.append(reply)
		else:
			reply = thread.replies[0]
			reply.comment = form.comment.data

		thread.title   = form.title.data

		db.session.commit()

		notif_msg = None
		if was_new:
			notif_msg = "New review '{}' on package {}".format(form.title.data, package.title)
		else:
			notif_msg = "Updated review '{}' on package {}".format(form.title.data, package.title)

		addNotification(package.maintainers, current_user, notif_msg, url_for("threads.view", id=thread.id))

		db.session.commit()

		return redirect(package.getDetailsURL())

	return render_template("packages/review_create_edit.html", form=form, package=package)
