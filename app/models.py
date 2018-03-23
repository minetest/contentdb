from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from app import app
from datetime import datetime
from sqlalchemy.orm import validates
from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter
import enum

# Initialise database
db = SQLAlchemy(app)


class UserRank(enum.Enum):
	NOT_JOINED = 0
	NEW_MEMBER = 1
	MEMBER     = 2
	EDITOR     = 3
	MODERATOR  = 4
	ADMIN      = 5

	def atLeast(self, min):
		return self.value >= min.value

	def getTitle(self):
		return self.name.replace("_", " ").title()


class Permission(enum.Enum):
	EDIT_PACKAGE       = "EDIT_PACKAGE"
	APPROVE_CHANGES    = "APPROVE_CHANGES"
	DELETE_PACKAGE     = "DELETE_PACKAGE"
	CHANGE_AUTHOR      = "CHANGE_AUTHOR"
	MAKE_RELEASE       = "MAKE_RELEASE"
	APPROVE_RELEASE    = "APPROVE_RELEASE"
	APPROVE_NEW        = "APPROVE_NEW"
	CHANGE_RELEASE_URL = "CHANGE_RELEASE_URL"

	# Only return true if the permission is valid for *all* contexts
	# See Package.checkPerm for package-specific contexts
	def check(self, user):
		if not user.is_authenticated:
			return False

		if self == Permission.APPROVE_NEW or \
				self == Permission.APPROVE_CHANGES or \
				self == Permission.APPROVE_RELEASE:
			return user.rank.atLeast(UserRank.EDITOR)
		else:
			raise Exception("Non-global permission checked globally. Use Package.checkPerm or User.checkPerm instead.")


class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)

	# User authentication information
	username = db.Column(db.String(50), nullable=False, unique=True)
	password = db.Column(db.String(255), nullable=False, server_default="")
	reset_password_token = db.Column(db.String(100), nullable=False, server_default="")

	rank = db.Column(db.Enum(UserRank))

	# Account linking
	github_username = db.Column(db.String(50), nullable=True, unique=True)
	forums_username = db.Column(db.String(50), nullable=True, unique=True)

	# User email information
	email = db.Column(db.String(255), nullable=True, unique=True)
	confirmed_at = db.Column(db.DateTime())

	# User information
	active = db.Column("is_active", db.Boolean, nullable=False, server_default="0")
	display_name = db.Column(db.String(100), nullable=False, server_default="")

	# Content
	packages = db.relationship("Package", backref="author", lazy="dynamic")

	def __init__(self, username):
		import datetime

		self.username = username
		self.confirmed_at = datetime.datetime.now() - datetime.timedelta(days=6000)
		self.display_name = username
		self.rank = UserRank.NOT_JOINED

	def isClaimed(self):
		return self.password is not None and self.password != ""

class PackageType(enum.Enum):
	MOD  = "Mod"
	GAME = "Game"
	TXP  = "Texture Pack"

	def toName(self):
		return self.name.lower()

	def __str__(self):
		return self.name

	@classmethod
	def choices(cls):
		return [(choice, choice.value) for choice in cls]

	@classmethod
	def coerce(cls, item):
		return item if type(item) == PackageType else PackageType[item]

class Package(db.Model):
	id           = db.Column(db.Integer, primary_key=True)

	# Basic details
	author_id    = db.Column(db.Integer, db.ForeignKey("user.id"))
	name         = db.Column(db.String(100), nullable=False)
	title        = db.Column(db.String(100), nullable=False)
	shortDesc    = db.Column(db.String(200), nullable=False)
	desc         = db.Column(db.Text, nullable=True)
	type         = db.Column(db.Enum(PackageType))

	approved     = db.Column(db.Boolean, nullable=False, default=False)

	# Downloads
	repo         = db.Column(db.String(200), nullable=True)
	website      = db.Column(db.String(200), nullable=True)
	issueTracker = db.Column(db.String(200), nullable=True)
	forums       = db.Column(db.Integer,     nullable=False)

	# Releases
	releases = db.relationship("PackageRelease", backref="package",
			lazy="dynamic", order_by=db.desc("package_release_releaseDate"))

	def getDetailsURL(self):
		return url_for("package_page",
				type=self.type.toName(),
				author=self.author.username, name=self.name)

	def getEditURL(self):
		return url_for("create_edit_package_page",
				type=self.type.toName(),
				author=self.author.username, name=self.name)

	def getApproveURL(self):
		return url_for("approve_package_page",
				type=self.type.toName(),
				author=self.author.username, name=self.name)

	def getCreateReleaseURL(self):
		return url_for("create_release_page",
				type=self.type.toName(),
				author=self.author.username, name=self.name)

	def getDownloadURL(self):
		return url_for("package_download_page",
				type=self.type.toName(),
				author=self.author.username, name=self.name)

	def getDownloadRelease(self):
		for rel in self.releases:
			if rel.approved:
				return rel

		return None

	def checkPerm(self, user, perm):
		if not user.is_authenticated:
			return False

		if type(perm) == str:
			perm = Permission[perm]
		elif type(perm) != Permission:
			raise Exception("Unknown permission given to Package.checkPerm()")

		isOwner = user == self.author

		# Members can edit their own packages, and editors can edit any packages
		if perm == Permission.MAKE_RELEASE:
			return isOwner or user.rank.atLeast(UserRank.EDITOR)

		if perm == Permission.EDIT_PACKAGE or perm == Permission.APPROVE_CHANGES:
			return user.rank.atLeast(UserRank.MEMBER if isOwner else UserRank.EDITOR)

		# Editors can change authors, approve new packages, and approve releases
		elif perm == Permission.CHANGE_AUTHOR or perm == Permission.APPROVE_NEW \
				or perm == Permission.APPROVE_RELEASE:
			return user.rank.atLeast(UserRank.EDITOR)

		# Moderators can delete packages
		elif perm == Permission.DELETE_PACKAGE or perm == Permission.CHANGE_RELEASE_URL:
			return user.rank.atLeast(UserRank.MODERATOR)

		else:
			raise Exception("Permission {} is not related to packages".format(perm.name))

class PackageRelease(db.Model):
	id           = db.Column(db.Integer, primary_key=True)

	package_id   = db.Column(db.Integer, db.ForeignKey("package.id"))
	title        = db.Column(db.String(100), nullable=False)
	releaseDate  = db.Column(db.DateTime,        nullable=False)
	url          = db.Column(db.String(100), nullable=False)
	approved     = db.Column(db.Boolean, nullable=False, default=False)


	def getEditURL(self):
		return url_for("edit_release_page",
				type=self.package.type.toName(),
				author=self.package.author.username,
				name=self.package.name,
				id=self.id)

	def __init__(self):
		self.releaseDate = datetime.now()

# Setup Flask-User
db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
user_manager = UserManager(db_adapter, app)     # Initialize Flask-User
