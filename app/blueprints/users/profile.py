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

import math

from flask import *
from flask_login import current_user, login_required
from sqlalchemy import func

from app.models import *
from app.tasks.forumtasks import checkForumAccount
from . import bp


@bp.route("/users/", methods=["GET"])
def list_all():
	users = db.session.query(User, func.count(Package.id)) \
			.select_from(User).outerjoin(Package) \
			.order_by(db.desc(User.rank), db.asc(User.display_name)) \
			.group_by(User.id).all()

	return render_template("users/list.html", users=users)


@bp.route("/user/forum/<username>/")
def by_forums_username(username):
	user = User.query.filter_by(forums_username=username).first()
	if user:
		return redirect(url_for("users.profile", username=user.username))

	return render_template("users/forums_no_such_user.html", username=username)


@bp.route("/users/<username>/")
def profile(username):
	user = User.query.filter_by(username=username).first()
	if not user:
		abort(404)

	if not current_user.is_authenticated or (user != current_user and not current_user.canAccessTodoList()):
		packages = user.packages.filter_by(state=PackageState.APPROVED)
		maintained_packages = user.maintained_packages.filter_by(state=PackageState.APPROVED)
	else:
		packages = user.packages.filter(Package.state != PackageState.DELETED)
		maintained_packages = user.maintained_packages.filter(Package.state != PackageState.DELETED)

	packages = packages.order_by(db.asc(Package.title)).all()
	maintained_packages = maintained_packages \
		.filter(Package.author != user) \
		.order_by(db.asc(Package.title)).all()

	users_by_reviews = db.session.query(User.username, func.count(PackageReview.id).label("count")) \
		.select_from(User).join(PackageReview) \
		.group_by(User.username).order_by(text("count DESC")).all()
	try:
		review_boundary = users_by_reviews[math.floor(len(users_by_reviews) * 0.25)][1] + 1
	except IndexError:
		review_boundary = None
	users_by_reviews = [ username for username, _ in users_by_reviews ]

	review_idx = None
	review_percent = None
	try:
		review_idx = users_by_reviews.index(user.username)
		review_percent = round(100 * review_idx / len(users_by_reviews), 1)
	except ValueError:
		pass

	total_downloads = db.session.query(func.sum(Package.downloads)) \
		.select_from(User) \
		.join(User.packages) \
		.filter(User.id == user.id, Package.state == PackageState.APPROVED).scalar() or 0

	all_package_ranks = db.session.query(
			Package.type,
			Package.author_id,
			func.rank().over(order_by=db.desc(Package.score), partition_by=Package.type) \
				.label('rank')).order_by(db.asc(text("rank"))) \
		.filter_by(state=PackageState.APPROVED).subquery()

	user_package_ranks = db.session.query(all_package_ranks) \
		.filter_by(author_id=user.id).first()
	min_package_rank = None
	min_package_type = None
	if user_package_ranks:
		min_package_rank = user_package_ranks[2]
		min_package_type = PackageType.coerce(user_package_ranks[0]).value

	# Process GET or invalid POST
	return render_template("users/profile.html", user=user,
			packages=packages, maintained_packages=maintained_packages,
			total_downloads=total_downloads,
			review_idx=review_idx, review_percent=review_percent, review_boundary=review_boundary,
			min_package_rank=min_package_rank, min_package_type=min_package_type)


@bp.route("/users/<username>/check/", methods=["POST"])
@login_required
def user_check(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)

	if current_user != user and not current_user.rank.atLeast(UserRank.MODERATOR):
		abort(403)

	if user.forums_username is None:
		abort(404)

	task = checkForumAccount.delay(user.forums_username)
	next_url = url_for("users.profile", username=username)

	return redirect(url_for("tasks.check", id=task.id, r=next_url))
