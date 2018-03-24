from flask import *
from flask_user import *
from flask_login import login_user, logout_user
from flask.ext import menu
from app import app
from app.models import *
from flask_wtf import FlaskForm
from flask_user.forms import RegisterForm
from wtforms import *
from wtforms.validators import *

class MyRegisterForm(RegisterForm):
	display_name = StringField("Display name")

# Define the User profile form
class UserProfileForm(FlaskForm):
	display_name = StringField("Display name")
	rank = SelectField("Rank", [InputRequired()], choices=UserRank.choices(), coerce=UserRank.coerce, default=UserRank.NEW_MEMBER)
	submit = SubmitField("Save")

@app.route("/users/", methods=["GET"])
def user_list_page():
	users = User.query.all()
	return render_template("users/list.html", users=users)


@app.route("/users/<username>/", methods=["GET", "POST"])
def user_profile_page(username):
	user = User.query.filter_by(username=username).first()
	if not user:
		abort(404)

	form = None
	if user == current_user or user.checkPerm(current_user, Permission.CHANGE_RANK):
		# Initialize form
		form = UserProfileForm(formdata=request.form, obj=user)

		# Process valid POST
		if request.method=="POST" and form.validate():
			# Copy form fields to user_profile fields
			if user == current_user:
				user.display_name = form["display_name"].data

			if user.checkPerm(current_user, Permission.CHANGE_RANK):
				newRank = form["rank"].data
				if current_user.rank.atLeast(newRank):
					user.rank = form["rank"].data
				else:
					flash("Can't promote a user to a rank higher than yourself!", "error")

			# Save user_profile
			db.session.commit()

			# Redirect to home page
			return redirect(url_for("user_profile_page", username=username))

	# Process GET or invalid POST
	return render_template("users/user_profile_page.html",
			user=user, form=form)
