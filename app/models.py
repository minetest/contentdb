from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from app import app
from datetime import datetime
from sqlalchemy.orm import validates
from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter
import enum

# Initialise database
db = SQLAlchemy(app)

def title_to_url(title):
	return title.lower().replace(" ", "_")

def url_to_title(url):
	return url.replace("_", " ")

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)

	# User authentication information
	username = db.Column(db.String(50), nullable=False, unique=True)
	password = db.Column(db.String(255), nullable=False, server_default='')
	reset_password_token = db.Column(db.String(100), nullable=False, server_default='')

	# Account linking
	github_username = db.Column(db.String(50), nullable=True, unique=True)
	forums_username = db.Column(db.String(50), nullable=True, unique=True)

	# User email information
	email = db.Column(db.String(255), nullable=True, unique=True)
	confirmed_at = db.Column(db.DateTime())

	# User information
	active = db.Column('is_active', db.Boolean, nullable=False, server_default='0')
	display_name = db.Column(db.String(100), nullable=False, server_default='')

	# Content
	packages = db.relationship('Package', backref='author', lazy='dynamic')

	def __init__(self, username):
		import datetime

		self.username = username
		self.confirmed_at = datetime.datetime.now() - datetime.timedelta(days=6000)
		self.display_name = username

	def isClaimed(self):
		return self.password is not None and self.password != ""

class Role(db.Model):
	id          = db.Column(db.Integer(), primary_key=True)
	name        = db.Column(db.String(50), unique=True)
	description = db.Column(db.String(255))

class UserRoles(db.Model):
	id      = db.Column(db.Integer(), primary_key=True)
	user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
	role_id = db.Column(db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))

class PackageType(enum.Enum):
	MOD  = "Mod"
	GAME = "Game"
	TXP  = "Texture Pack"

	def getTitle(self):
		if self == PackageType.MOD:
			return "Mod"
		elif self == PackageType.GAME:
			return "Game"
		else:
			return "TXP"

	@staticmethod
	def fromName(name):
		if name == "mod":
			return PackageType.MOD
		elif name == "game":
			return PackageType.GAME
		elif name == "texturepacks":
			return PackageType.TXP
		else:
			return None

class Package(db.Model):
	id           = db.Column(db.Integer, primary_key=True)

	# Basic details
	author_id    = db.Column(db.Integer, db.ForeignKey('user.id'))
	name         = db.Column(db.String(100), nullable=False)
	title        = db.Column(db.String(100), nullable=False)
	desc         = db.Column(db.Text, nullable=True)
	type         = db.Column(db.Enum(PackageType))

	# Downloads
	repo         = db.Column(db.String(200), nullable=True)
	website      = db.Column(db.String(200), nullable=True)
	issueTracker = db.Column(db.String(200), nullable=True)
	forums       = db.Column(db.String(200), nullable=False)

# Setup Flask-User
db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
user_manager = UserManager(db_adapter, app)     # Initialize Flask-User
