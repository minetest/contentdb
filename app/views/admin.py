from flask import *
from flask_user import *
from flask.ext import menu
from app import app
from app.models import *
from app.tasks.forumtasks import importUsersFromModList
from flask_wtf import FlaskForm
from wtforms import *
from app.utils import loginUser, rank_required

@menu.register_menu(app, ".admin", "Admin", order=30,
		visible_when=lambda: current_user.rank.atLeast(UserRank.ADMIN))
@app.route("/admin/", methods=["GET", "POST"])
@rank_required(UserRank.ADMIN)
def admin_page():
	if request.method == "POST":
		action = request.form["action"]
		if action == "importusers":
			task = importUsersFromModList.delay()
			return redirect(url_for("check_task", id=task.id, r=url_for("user_list_page")))
		else:
			flash("Unknown action: " + action, "error")

	return render_template("admin/list.html")

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
