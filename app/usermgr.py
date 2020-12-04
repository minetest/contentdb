from . import app
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "users.login"

class UserMixin:
	is_authenticated = True
	is_anonymous = False
