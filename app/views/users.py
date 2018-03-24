from flask import *
from flask_user import *
from flask_login import login_user, logout_user
from flask.ext import menu
from app import app
from app.models import *



# Define the User registration form
# It augments the Flask-User RegisterForm with additional fields
from flask_user.forms import RegisterForm
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators
class MyRegisterForm(RegisterForm):
	display_name = StringField("Display name")

# Define the User profile form
class UserProfileForm(FlaskForm):
	display_name = StringField("Display name")
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
	if user == current_user:
		# Initialize form
		form = UserProfileForm(formdata=request.form, obj=current_user)

		# Process valid POST
		if request.method=="POST" and form.validate():
			# Copy form fields to user_profile fields
			form.populate_obj(current_user)

			# Save user_profile
			db.session.commit()

			# Redirect to home page
			return redirect(url_for("home_page"))

	# Process GET or invalid POST
	return render_template("users/user_profile_page.html",
			user=user, form=form)
