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

class UserRank(enum.Enum):
	NEW_MEMBER = 0
	MEMBER     = 1
	EDITOR     = 2
	MODERATOR  = 3
	ADMIN      = 4

	def atLeast(self, min):
		return self.value >= min.value

	def getTitle(self):
		return self.name.replace("_", " ").title()

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)

	# User authentication information
	username = db.Column(db.String(50), nullable=False, unique=True)
	password = db.Column(db.String(255), nullable=False, server_default='')
	reset_password_token = db.Column(db.String(100), nullable=False, server_default='')

	rank = db.Column(db.Enum(UserRank))

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
		self.rank = UserRank.MEMBER

	def isClaimed(self):
		return self.password is not None and self.password != ""

class Permission(enum.Enum):
	EDIT_PACKAGE    = "EDIT_PACKAGE"
	APPROVE_CHANGES = "APPROVE_CHANGES"
	DELETE_PACKAGE  = "DELETE_PACKAGE"
	CHANGE_AUTHOR   = "CHANGE_AUTHOR"
	APPROVE_RELEASE = "APPROVE_RELEASE"
	APPROVE_NEW     = "APPROVE_NEW"

class PackageType(enum.Enum):
	MOD  = "Mod"
	GAME = "Game"
	TXP  = "Texture Pack"

	def toName(self):
		return self.value.lower().replace(" ", "")

	@staticmethod
	def fromName(name):
		if name == "mod":
			return PackageType.MOD
		elif name == "game":
			return PackageType.GAME
		elif name == "texturepack":
			return PackageType.TXP
		else:
			return None

	@classmethod
	def choices(cls):
		return [(choice, choice.value) for choice in cls]

	@classmethod
	def coerce(cls, item):
		"""item will be both type(enum) AND type(unicode).
		"""
		if item == 'PackageType.MOD' or item == PackageType.MOD:
			return PackageType.MOD
		elif item == 'PackageType.GAME' or item == PackageType.GAME:
			return PackageType.GAME
		elif item == 'PackageType.TXP' or item == PackageType.TXP:
			return PackageType.TXP
		else:
			print("Can't coerce", item, type(item))

class Package(db.Model):
	id           = db.Column(db.Integer, primary_key=True)

	# Basic details
	author_id    = db.Column(db.Integer, db.ForeignKey('user.id'))
	name         = db.Column(db.String(100), nullable=False)
	title        = db.Column(db.String(100), nullable=False)
	shortDesc    = db.Column(db.Text, nullable=True)
	desc         = db.Column(db.Text, nullable=True)
	type         = db.Column(db.Enum(PackageType))

	# Downloads
	repo         = db.Column(db.String(200), nullable=True)
	website      = db.Column(db.String(200), nullable=True)
	issueTracker = db.Column(db.String(200), nullable=True)
	forums       = db.Column(db.String(200), nullable=False)

	def getDetailsURL(self):
		return url_for("package_page",
				type=self.type.toName(),
				author=self.author.username, name=self.name)

	def getEditURL(self):
		return url_for("edit_package_page",
				type=self.type.toName(),
				author=self.author.username, name=self.name)

	def checkPerm(self, user, perm):
		if not user.is_authenticated:
			return False

		if type(perm) == str:
			perm = Permission[perm]
		elif type(perm) != Permission:
			raise Exception("Unknown permission given to Package.checkPerm()")

		isOwner = user == self.author

		# Members can edit their own packages, and editors can edit any packages
		if perm == Permission.EDIT_PACKAGE or perm == Permission.APPROVE_CHANGES:
			return user.rank.atLeast(UserRank.MEMBER if isOwner else UserRank.EDITOR)

		# Editors can change authors, approve new packages, and approve releases
		elif perm == Permission.CHANGE_AUTHOR or perm == Permission.APPROVE_NEW \
				or perm == Permission.APPROVE_RELEASE:
			return user.rank.atLeast(UserRank.EDITOR)

		# Moderators can delete packages
		elif perm == Permission.DELETE_PACKAGE:
			return user.rank.atLeast(UserRank.MODERATOR)

		else:
			raise Exception("Permission {} is not related to packages".format(perm.name))

# Setup Flask-User
db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
user_manager = UserManager(db_adapter, app)     # Initialize Flask-User
