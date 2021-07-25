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

	packages = user.packages.filter(Package.state != PackageState.DELETED)
	if not current_user.is_authenticated or (user != current_user and not current_user.canAccessTodoList()):
		packages = packages.filter_by(state=PackageState.APPROVED)
	packages = packages.order_by(db.asc(Package.title))

	users_by_reviews = db.session.query(User.username, func.count(PackageReview.id).label("count")) \
		.select_from(User).join(PackageReview) \
		.group_by(User.username).order_by(text("count DESC")).all()
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
		.join(User.maintained_packages) \
		.filter(User.id == user.id, Package.state == PackageState.APPROVED).scalar() or 0

	all_package_ranks = db.session.query(
			Package.author_id,
			func.rank().over(order_by=db.desc(Package.score)) \
				.label('rank')).order_by(db.asc(text("rank"))).subquery()
	user_package_ranks = db.session.query(all_package_ranks) \
		.filter_by(author_id=user.id).first()
	min_package_rank = user_package_ranks[1] if user_package_ranks else None

	# Process GET or invalid POST
	return render_template("users/profile.html", user=user, packages=packages,
			total_downloads=total_downloads, min_package_rank=min_package_rank,
			review_idx=review_idx, review_percent=review_percent)


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
