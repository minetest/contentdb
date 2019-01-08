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
import flask_menu as menu
from app import app
from app.models import *
from celery import uuid
from app.tasks.importtasks import importRepoScreenshot, importAllDependencies, makeVCSRelease
from app.tasks.forumtasks  import importTopicList, checkAllForumAccounts
from flask_wtf import FlaskForm
from wtforms import *
from app.utils import loginUser, rank_required, triggerNotif
import datetime

@app.route("/admin/", methods=["GET", "POST"])
@rank_required(UserRank.ADMIN)
def admin_page():
	if request.method == "POST":
		action = request.form["action"]
		if action == "importmodlist":
			task = importTopicList.delay()
			return redirect(url_for("check_task", id=task.id, r=url_for("todo_topics_page")))
		elif action == "checkusers":
			task = checkAllForumAccounts.delay()
			return redirect(url_for("check_task", id=task.id, r=url_for("admin_page")))
		elif action == "importscreenshots":
			packages = Package.query \
				.filter_by(soft_deleted=False) \
				.outerjoin(PackageScreenshot, Package.id==PackageScreenshot.package_id) \
				.filter(PackageScreenshot.id==None) \
				.all()
			for package in packages:
				importRepoScreenshot.delay(package.id)

			return redirect(url_for("admin_page"))
		elif action == "restore":
			package = Package.query.get(request.form["package"])
			if package is None:
				flash("Unknown package", "error")
			else:
				package.soft_deleted = False
				db.session.commit()
				return redirect(url_for("admin_page"))
		elif action == "importdepends":
			task = importAllDependencies.delay()
			return redirect(url_for("check_task", id=task.id, r=url_for("admin_page")))
		elif action == "modprovides":
			packages = Package.query.filter_by(type=PackageType.MOD).all()
			mpackage_cache = {}
			for p in packages:
				if len(p.provides) == 0:
					p.provides.append(MetaPackage.GetOrCreate(p.name, mpackage_cache))

			db.session.commit()
			return redirect(url_for("admin_page"))
		elif action == "recalcscores":
			for p in Package.query.all():
				p.recalcScore()

			db.session.commit()
			return redirect(url_for("admin_page"))
		elif action == "vcsrelease":
			for package in Package.query.filter(Package.repo.isnot(None)).all():
				if package.releases.count() != 0:
					continue

				rel = PackageRelease()
				rel.package  = package
				rel.title    = datetime.date.today().isoformat()
				rel.url      = ""
				rel.task_id  = uuid()
				rel.approved = True
				db.session.add(rel)
				db.session.commit()

				makeVCSRelease.apply_async((rel.id, "master"), task_id=rel.task_id)

				msg = "{}: Release {} created".format(package.title, rel.title)
				triggerNotif(package.author, current_user, msg, rel.getEditURL())
				db.session.commit()

		else:
			flash("Unknown action: " + action, "error")

	deleted_packages = Package.query.filter_by(soft_deleted=True).all()
	return render_template("admin/list.html", deleted_packages=deleted_packages)

class SwitchUserForm(FlaskForm):
	username = StringField("Username")
	submit = SubmitField("Switch")


@app.route("/admin/switchuser/", methods=["GET", "POST"])
@rank_required(UserRank.ADMIN)
def switch_user_page():
	form = SwitchUserForm(formdata=request.form)
	if request.method == "POST" and form.validate():
		user = User.query.filter_by(username=form["username"].data).first()
		if user is None:
			flash("Unable to find user", "error")
		elif loginUser(user):
			return redirect(url_for("user_profile_page", username=current_user.username))
		else:
			flash("Unable to login as user", "error")


	# Process GET or invalid POST
	return render_template("admin/switch_user_page.html", form=form)
