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
	first_name = StringField('First name', validators=[
		validators.DataRequired('First name is required')])
	last_name = StringField('Last name', validators=[
		validators.DataRequired('Last name is required')])

# Define the User profile form
class UserProfileForm(FlaskForm):
	first_name = StringField('First name', validators=[
		validators.DataRequired('First name is required')])
	last_name = StringField('Last name', validators=[
		validators.DataRequired('Last name is required')])
	submit = SubmitField('Save')

@app.route('/user/', methods=['GET', 'POST'])
@app.route('/user/<username>/', methods=['GET'])
def user_profile_page(username=None):
	user = None
	form = None
	if username is None:
		if not current_user.is_authenticated:
			return current_app.login_manager.unauthorized()
		user = current_user
	else:
		user = User.query.filter_by(username=username).first()
		if not user:
			abort(404)

	if user == current_user:
		# Initialize form
		form = UserProfileForm(request.form, current_user)

		# Process valid POST
		if request.method=='POST' and form.validate():
			# Copy form fields to user_profile fields
			form.populate_obj(current_user)

			# Save user_profile
			db.session.commit()

			# Redirect to home page
			return redirect(url_for('home_page'))

	# Process GET or invalid POST
	return render_template('users/user_profile_page.html',
			user=user, form=form)
