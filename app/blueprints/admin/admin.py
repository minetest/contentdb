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


import os

from celery import group
from flask import *
from flask_login import current_user, login_user
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import InputRequired, Length

from app.models import *
from app.tasks.forumtasks import importTopicList, checkAllForumAccounts
from app.tasks.importtasks import importRepoScreenshot, checkZipRelease, updateMetaFromRelease, importForeignDownloads
from app.utils import rank_required, addAuditLog, addNotification
from . import bp


@bp.route("/admin/", methods=["GET", "POST"])
@rank_required(UserRank.ADMIN)
def admin_page():
	if request.method == "POST":
		action = request.form["action"]

		if action == "delstuckreleases":
			PackageRelease.query.filter(PackageRelease.task_id != None).delete()
			db.session.commit()
			return redirect(url_for("admin.admin_page"))

		elif action == "checkreleases":
			releases = PackageRelease.query.filter(PackageRelease.url.like("/uploads/%")).all()

			tasks = []
			for release in releases:
				zippath = release.url.replace("/uploads/", app.config["UPLOAD_DIR"])
				tasks.append(checkZipRelease.s(release.id, zippath))

			result = group(tasks).apply_async()

			while not result.ready():
				import time
				time.sleep(0.1)

			return redirect(url_for("todo.view"))

		elif action == "reimportpackages":
			tasks = []
			for package in Package.query.filter(Package.state!=PackageState.DELETED).all():
				release = package.releases.first()
				if release:
					zippath = release.url.replace("/uploads/", app.config["UPLOAD_DIR"])
					tasks.append(updateMetaFromRelease.s(release.id, zippath))

			result = group(tasks).apply_async()

			while not result.ready():
				import time
				time.sleep(0.1)

			return redirect(url_for("todo.view"))

		elif action == "importforeign":
			releases = PackageRelease.query.filter(PackageRelease.url.like("http%")).all()

			tasks = []
			for release in releases:
				tasks.append(importForeignDownloads.s(release.id))

			result = group(tasks).apply_async()

			while not result.ready():
				import time
				time.sleep(0.1)

			return redirect(url_for("todo.view"))

		elif action == "importmodlist":
			task = importTopicList.delay()
			return redirect(url_for("tasks.check", id=task.id, r=url_for("todo.topics")))

		elif action == "checkusers":
			task = checkAllForumAccounts.delay()
			return redirect(url_for("tasks.check", id=task.id, r=url_for("admin.admin_page")))

		elif action == "importscreenshots":
			packages = Package.query \
				.filter(Package.state!=PackageState.DELETED) \
				.outerjoin(PackageScreenshot, Package.id==PackageScreenshot.package_id) \
				.filter(PackageScreenshot.id==None) \
				.all()
			for package in packages:
				importRepoScreenshot.delay(package.id)

			return redirect(url_for("admin.admin_page"))

		elif action == "restore":
			package = Package.query.get(request.form["package"])
			if package is None:
				flash("Unknown package", "danger")
			else:
				package.state = PackageState.READY_FOR_REVIEW
				db.session.commit()
				return redirect(url_for("admin.admin_page"))

		elif action == "recalcscores":
			for p in Package.query.all():
				p.recalcScore()

			db.session.commit()
			return redirect(url_for("admin.admin_page"))

		elif action == "cleanuploads":
			upload_dir = app.config['UPLOAD_DIR']

			(_, _, filenames) = next(os.walk(upload_dir))
			existing_uploads = set(filenames)

			if len(existing_uploads) != 0:
				def getURLsFromDB(column):
					results = db.session.query(column).filter(column != None, column != "").all()
					return set([os.path.basename(x[0]) for x in results])

				release_urls = getURLsFromDB(PackageRelease.url)
				screenshot_urls = getURLsFromDB(PackageScreenshot.url)

				db_urls = release_urls.union(screenshot_urls)
				unreachable = existing_uploads.difference(db_urls)

				import sys
				print("On Disk: ", existing_uploads, file=sys.stderr)
				print("In DB: ", db_urls, file=sys.stderr)
				print("Unreachable: ", unreachable, file=sys.stderr)

				for filename in unreachable:
					os.remove(os.path.join(upload_dir, filename))

				flash("Deleted " + str(len(unreachable)) + " unreachable uploads", "success")
			else:
				flash("No downloads to create", "danger")

			return redirect(url_for("admin.admin_page"))

		elif action == "delmetapackages":
			query = MetaPackage.query.filter(~MetaPackage.dependencies.any(), ~MetaPackage.packages.any())
			count = query.count()
			query.delete(synchronize_session=False)
			db.session.commit()

			flash("Deleted " + str(count) + " unused meta packages", "success")
			return redirect(url_for("admin.admin_page"))
		else:
			flash("Unknown action: " + action, "danger")

	deleted_packages = Package.query.filter(Package.state==PackageState.DELETED).all()
	return render_template("admin/list.html", deleted_packages=deleted_packages)

class SwitchUserForm(FlaskForm):
	username = StringField("Username")
	submit = SubmitField("Switch")


@bp.route("/admin/switchuser/", methods=["GET", "POST"])
@rank_required(UserRank.ADMIN)
def switch_user():
	form = SwitchUserForm(formdata=request.form)
	if form.validate_on_submit():
		user = User.query.filter_by(username=form["username"].data).first()
		if user is None:
			flash("Unable to find user", "danger")
		elif login_user(user):
			return redirect(url_for("users.profile", username=current_user.username))
		else:
			flash("Unable to login as user", "danger")


	# Process GET or invalid POST
	return render_template("admin/switch_user.html", form=form)


class SendNotificationForm(FlaskForm):
	title  = StringField("Title", [InputRequired(), Length(1, 300)])
	url    = StringField("URL", [InputRequired(), Length(1, 100)], default="/")
	submit = SubmitField("Send")


@bp.route("/admin/send-notification/", methods=["GET", "POST"])
@rank_required(UserRank.ADMIN)
def send_bulk_notification():
	form = SendNotificationForm(request.form)
	if form.validate_on_submit():
		addAuditLog(AuditSeverity.MODERATION, current_user,
				"Sent bulk notification", None, None, form.title.data)

		users = User.query.filter(User.rank >= UserRank.NEW_MEMBER).all()
		addNotification(users, current_user, NotificationType.OTHER, form.title.data, form.url.data, None)
		db.session.commit()

		return redirect(url_for("admin.admin_page"))

	return render_template("admin/send_bulk_notification.html", form=form)
