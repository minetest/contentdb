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
from typing import Optional

from flask import *
from flask_babel import gettext
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


class Medal:
	description: str
	color: Optional[str]
	icon: str
	title: Optional[str]
	progress: Optional[Tuple[int, int]]

	def __init__(self, description: str, **kwargs):
		self.description = description
		self.color = kwargs.get("color", "white")
		self.icon = kwargs.get("icon", None)
		self.title = kwargs.get("title", None)
		self.progress = kwargs.get("progress", None)

	@classmethod
	def make_unlocked(cls, color: str, icon: str, title: str, description: str):
		return Medal(description=description, color=color, icon=icon, title=title)

	@classmethod
	def make_locked(cls, description: str, progress: Tuple[int, int]):
		if progress[0] is None or progress[1] is None:
			raise Exception("Invalid progress")

		return Medal(description=description, progress=progress)


def place_to_color(place: int) -> str:
	if place == 1:
		return "gold"
	elif place == 2:
		return "#888"
	elif place == 3:
		return "#cd7f32"
	else:
		return "white"


def get_user_medals(user: User) -> Tuple[List[Medal], List[Medal]]:
	unlocked = []
	locked = []

	#
	# REVIEWS
	#

	users_by_reviews = db.session.query(User.username, func.sum(PackageReview.score).label("karma")) \
		.select_from(User).join(PackageReview) \
		.group_by(User.username).order_by(text("karma DESC")).all()
	try:
		review_boundary = users_by_reviews[math.floor(len(users_by_reviews) * 0.25)][1] + 1
	except IndexError:
		review_boundary = None
	usernames_by_reviews = [username for username, _ in users_by_reviews]

	review_idx = None
	review_percent = None
	review_karma = 0
	try:
		review_idx = usernames_by_reviews.index(user.username)
		review_percent = round(100 * review_idx / len(users_by_reviews), 1)
		review_karma = max(users_by_reviews[review_idx][1], 0)
	except ValueError:
		pass

	if review_percent is not None and review_percent < 25:
		if review_idx == 0:
			title = gettext(u"Top reviewer")
			description = gettext(
					u"%(display_name)s has written the most helpful reviews on ContentDB.",
					display_name=user.display_name)
		elif review_idx <= 2:
			if review_idx == 1:
				title = gettext(u"2nd most helpful reviewer")
			else:
				title = gettext(u"3rd most helpful reviewer")
			description = gettext(
					u"This puts %(display_name)s in the top %(perc)s%%",
					display_name=user.display_name, perc=review_percent)
		else:
			title = gettext(u"Top %(perc)s%% reviewer", perc=review_percent)
			description = gettext(u"Only %(place)d users have written more helpful reviews.", place=review_idx)

		unlocked.append(Medal.make_unlocked(
				place_to_color(review_idx + 1), "fa-star-half-alt", title, description))
	elif review_boundary is not None:
		description = gettext(u"Consider writing more helpful reviews to get a medal.")
		if review_idx:
			description += " " + gettext(u"You are in place %(place)s.", place=review_idx + 1)
		locked.append(Medal.make_locked(
				description, (review_karma, review_boundary)))

	#
	# TOP PACKAGES
	#
	all_package_ranks = db.session.query(
			Package.type,
			Package.author_id,
			func.rank().over(
					order_by=db.desc(Package.score),
					partition_by=Package.type) \
				.label("rank")).order_by(db.asc(text("rank"))) \
		.filter_by(state=PackageState.APPROVED).subquery()

	user_package_ranks = db.session.query(all_package_ranks) \
		.filter_by(author_id=user.id) \
		.filter(text("rank <= 30")) \
		.all()

	user_package_ranks = next(
			(x for x in user_package_ranks if x[0] == PackageType.MOD or x[2] <= 10),
			None)
	if user_package_ranks:
		top_rank = user_package_ranks[2]
		top_type = PackageType.coerce(user_package_ranks[0])
		if top_rank == 1:
			title = gettext(u"Top %(type)s", type=top_type.text.lower())
		else:
			title = gettext(u"Top %(group)d %(type)s", group=top_rank, type=top_type.text.lower())
		if top_type == PackageType.MOD:
			icon = "fa-box"
		elif top_type == PackageType.GAME:
			icon = "fa-gamepad"
		else:
			icon = "fa-paint-brush"

		description = gettext(u"%(display_name)s has a %(type)s placed at #%(place)d.",
				display_name=user.display_name, type=top_type.text.lower(), place=top_rank)
		unlocked.append(
				Medal.make_unlocked(place_to_color(top_rank), icon, title, description))

	#
	# DOWNLOADS
	#
	total_downloads = db.session.query(func.sum(Package.downloads)) \
		.select_from(User) \
		.join(User.packages) \
		.filter(User.id == user.id,
			Package.state == PackageState.APPROVED).scalar()
	if total_downloads is None:
		pass
	elif total_downloads < 50000:
		description = gettext(u"Your packages have %(downloads)d downloads in total.", downloads=total_downloads)
		description += " " + gettext(u"First medal is at 50k.")
		locked.append(Medal.make_locked(description, (total_downloads, 50000)))
	else:
		if total_downloads >= 300000:
			place = 1
			title = gettext(u">300k downloads")
		elif total_downloads >= 100000:
			place = 2
			title = gettext(u">100k downloads")
		elif total_downloads >= 75000:
			place = 3
			title = gettext(u">75k downloads")
		else:
			place = 10
			title = gettext(u">50k downloads")
		description = gettext(u"Has received %(downloads)d downloads across all packages.",
				display_name=user.display_name, downloads=total_downloads)
		unlocked.append(Medal.make_unlocked(place_to_color(place), "fa-users", title, description))

	return unlocked, locked


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

	unlocked, locked = get_user_medals(user)
	# Process GET or invalid POST
	return render_template("users/profile.html", user=user,
			packages=packages, maintained_packages=maintained_packages,
			medals_unlocked=unlocked, medals_locked=locked)


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


@bp.route("/users/<username>/stats/")
def statistics(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)

	downloads = db.session.query(func.sum(Package.downloads)).filter(Package.author==user).one()

	return render_template("users/stats.html", user=user, downloads=downloads[0])
