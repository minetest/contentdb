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


from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from urllib.parse import urlparse
from app import app, gravatar
from sqlalchemy.orm import validates
from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter
import enum, datetime

# Initialise database
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class UserRank(enum.Enum):
	BANNED         = 0
	NOT_JOINED     = 1
	NEW_MEMBER     = 2
	MEMBER         = 3
	TRUSTED_MEMBER = 4
	EDITOR         = 5
	MODERATOR      = 6
	ADMIN          = 7

	def atLeast(self, min):
		return self.value >= min.value

	def getTitle(self):
		return self.name.replace("_", " ").title()

	def toName(self):
		return self.name.lower()

	def __str__(self):
		return self.name

	@classmethod
	def choices(cls):
		return [(choice, choice.getTitle()) for choice in cls]

	@classmethod
	def coerce(cls, item):
		return item if type(item) == UserRank else UserRank[item]


class Permission(enum.Enum):
	EDIT_PACKAGE       = "EDIT_PACKAGE"
	APPROVE_CHANGES    = "APPROVE_CHANGES"
	DELETE_PACKAGE     = "DELETE_PACKAGE"
	CHANGE_AUTHOR      = "CHANGE_AUTHOR"
	MAKE_RELEASE       = "MAKE_RELEASE"
	ADD_SCREENSHOTS    = "ADD_SCREENSHOTS"
	APPROVE_SCREENSHOT = "APPROVE_SCREENSHOT"
	APPROVE_RELEASE    = "APPROVE_RELEASE"
	APPROVE_NEW        = "APPROVE_NEW"
	CHANGE_RELEASE_URL = "CHANGE_RELEASE_URL"
	CHANGE_DNAME       = "CHANGE_DNAME"
	CHANGE_RANK        = "CHANGE_RANK"
	CHANGE_EMAIL       = "CHANGE_EMAIL"
	EDIT_EDITREQUEST   = "EDIT_EDITREQUEST"
	SEE_THREAD         = "SEE_THREAD"
	CREATE_THREAD      = "CREATE_THREAD"
	UNAPPROVE_PACKAGE  = "UNAPPROVE_PACKAGE"
	TOPIC_DISCARD      = "TOPIC_DISCARD"

	# Only return true if the permission is valid for *all* contexts
	# See Package.checkPerm for package-specific contexts
	def check(self, user):
		if not user.is_authenticated:
			return False

		if self == Permission.APPROVE_NEW or \
				self == Permission.APPROVE_CHANGES    or \
				self == Permission.APPROVE_RELEASE    or \
				self == Permission.APPROVE_SCREENSHOT or \
				self == Permission.SEE_THREAD:
			return user.rank.atLeast(UserRank.EDITOR)
		else:
			raise Exception("Non-global permission checked globally. Use Package.checkPerm or User.checkPerm instead.")

class User(db.Model, UserMixin):
	id           = db.Column(db.Integer, primary_key=True)

	# User authentication information
	username     = db.Column(db.String(50, collation="NOCASE"), nullable=False, unique=True, index=True)
	password     = db.Column(db.String(255), nullable=True)
	reset_password_token = db.Column(db.String(100), nullable=False, server_default="")

	rank         = db.Column(db.Enum(UserRank))

	# Account linking
	github_username = db.Column(db.String(50, collation="NOCASE"), nullable=True, unique=True)
	forums_username = db.Column(db.String(50, collation="NOCASE"), nullable=True, unique=True)

	# User email information
	email         = db.Column(db.String(255), nullable=True, unique=True)
	confirmed_at  = db.Column(db.DateTime())

	# User information
	profile_pic   = db.Column(db.String(255), nullable=True, server_default=None)
	active        = db.Column("is_active", db.Boolean, nullable=False, server_default="0")
	display_name  = db.Column(db.String(100), nullable=False, server_default="")

	# Content
	notifications = db.relationship("Notification", primaryjoin="User.id==Notification.user_id")

	# causednotifs  = db.relationship("Notification", backref="causer", lazy="dynamic")
	packages      = db.relationship("Package", backref="author", lazy="dynamic")
	requests      = db.relationship("EditRequest", backref="author", lazy="dynamic")
	threads       = db.relationship("Thread", backref="author", lazy="dynamic")
	replies       = db.relationship("ThreadReply", backref="author", lazy="dynamic")

	def __init__(self, username, active=False, email=None, password=None):
		self.username = username
		self.confirmed_at = datetime.datetime.now() - datetime.timedelta(days=6000)
		self.display_name = username
		self.active = active
		self.email = email
		self.password = password
		self.rank = UserRank.NOT_JOINED

	def canAccessTodoList(self):
		return Permission.APPROVE_NEW.check(self) or \
				Permission.APPROVE_RELEASE.check(self) or \
				Permission.APPROVE_CHANGES.check(self)

	def isClaimed(self):
		return self.rank.atLeast(UserRank.NEW_MEMBER)

	def getProfilePicURL(self):
		if self.profile_pic:
			return self.profile_pic
		else:
			return gravatar(self.email or "")

	def checkPerm(self, user, perm):
		if not user.is_authenticated:
			return False

		if type(perm) == str:
			perm = Permission[perm]
		elif type(perm) != Permission:
			raise Exception("Unknown permission given to User.checkPerm()")

		# Members can edit their own packages, and editors can edit any packages
		if perm == Permission.CHANGE_AUTHOR:
			return user.rank.atLeast(UserRank.EDITOR)
		elif perm == Permission.CHANGE_RANK or perm == Permission.CHANGE_DNAME:
			return user.rank.atLeast(UserRank.MODERATOR)
		elif perm == Permission.CHANGE_EMAIL:
			return user == self or (user.rank.atLeast(UserRank.MODERATOR) and user.rank.atLeast(self.rank))
		else:
			raise Exception("Permission {} is not related to users".format(perm.name))

	def canCommentRL(self):
		hour_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
		return ThreadReply.query.filter_by(author=self) \
			.filter(ThreadReply.created_at > hour_ago).count() < 4

	def canOpenThreadRL(self):
		hour_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
		return Thread.query.filter_by(author=self) \
			.filter(Thread.created_at > hour_ago).count() < 2

class UserEmailVerification(db.Model):
	id      = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
	email   = db.Column(db.String(100))
	token   = db.Column(db.String(32))
	user    = db.relationship("User", foreign_keys=[user_id])

class Notification(db.Model):
	id        = db.Column(db.Integer, primary_key=True)
	user_id   = db.Column(db.Integer, db.ForeignKey("user.id"))
	causer_id = db.Column(db.Integer, db.ForeignKey("user.id"))
	user      = db.relationship("User", foreign_keys=[user_id])
	causer    = db.relationship("User", foreign_keys=[causer_id])

	title     = db.Column(db.String(100), nullable=False)
	url       = db.Column(db.String(200), nullable=True)

	def __init__(self, us, cau, titl, ur):
		self.user   = us
		self.causer = cau
		self.title  = titl
		self.url    = ur


class License(db.Model):
	id      = db.Column(db.Integer, primary_key=True)
	name    = db.Column(db.String(50), nullable=False, unique=True)
	is_foss = db.Column(db.Boolean,    nullable=False, default=True)

	def __init__(self, v, is_foss=True):
		self.name = v
		self.is_foss = is_foss

	def __str__(self):
		return self.name


class PackageType(enum.Enum):
	MOD  = "Mod"
	GAME = "Game"
	TXP  = "Texture Pack"

	def toName(self):
		return self.name.lower()

	def __str__(self):
		return self.name

	@classmethod
	def get(cls, name):
		try:
			return PackageType[name.upper()]
		except KeyError:
			return None

	@classmethod
	def choices(cls):
		return [(choice, choice.value) for choice in cls]

	@classmethod
	def coerce(cls, item):
		return item if type(item) == PackageType else PackageType[item]


class PackagePropertyKey(enum.Enum):
	name          = "Name"
	title         = "Title"
	shortDesc     = "Short Description"
	desc          = "Description"
	type          = "Type"
	license       = "License"
	media_license = "Media License"
	tags          = "Tags"
	provides      = "Provides"
	repo          = "Repository"
	website       = "Website"
	issueTracker  = "Issue Tracker"
	forums        = "Forum Topic ID"

	def convert(self, value):
		if self == PackagePropertyKey.tags:
			return ",".join([t.title for t in value])
		elif self == PackagePropertyKey.provides:
			return ",".join([t.name for t in value])
		else:
			return str(value)

provides = db.Table("provides",
	db.Column("package_id",    db.Integer, db.ForeignKey("package.id"), primary_key=True),
    db.Column("metapackage_id", db.Integer, db.ForeignKey("meta_package.id"), primary_key=True)
)

tags = db.Table("tags",
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
    db.Column("package_id", db.Integer, db.ForeignKey("package.id"), primary_key=True)
)

class Dependency(db.Model):
	id              = db.Column(db.Integer, primary_key=True)
	depender_id     = db.Column(db.Integer, db.ForeignKey("package.id"),     nullable=True)
	package_id      = db.Column(db.Integer, db.ForeignKey("package.id"),     nullable=True)
	package         = db.relationship("Package", foreign_keys=[package_id])
	meta_package_id = db.Column(db.Integer, db.ForeignKey("meta_package.id"), nullable=True)
	optional        = db.Column(db.Boolean, nullable=False, default=False)
	__table_args__  = (db.UniqueConstraint('depender_id', 'package_id', 'meta_package_id', name='_dependency_uc'), )

	def __init__(self, depender=None, package=None, meta=None):
		if depender is None:
			return

		self.depender = depender

		packageProvided = package is not None
		metaProvided = meta is not None

		if packageProvided and not metaProvided:
			self.package = package
		elif metaProvided and not packageProvided:
			self.meta_package = meta
		else:
			raise Exception("Either meta or package must be given, but not both!")

	def __str__(self):
		if self.package is not None:
			return self.package.author.username + "/" + self.package.name
		elif self.meta_package is not None:
			return self.meta_package.name
		else:
			raise Exception("Meta and package are both none!")

	@staticmethod
	def SpecToList(depender, spec, cache={}):
		retval = []
		arr = spec.split(",")

		import re
		pattern1 = re.compile("^([a-z0-9_]+)$")
		pattern2 = re.compile("^([A-Za-z0-9_]+)/([a-z0-9_]+)$")

		for x in arr:
			x = x.strip()
			if x == "":
				continue

			if pattern1.match(x):
				meta = MetaPackage.GetOrCreate(x, cache)
				retval.append(Dependency(depender, meta=meta))
			else:
				m = pattern2.match(x)
				username = m.group(1)
				name     = m.group(2)
				user = User.query.filter_by(username=username).first()
				if user is None:
					raise Exception("Unable to find user " + username)

				package = Package.query.filter_by(author=user, name=name).first()
				if package is None:
					raise Exception("Unable to find package " + name + " by " + username)

				retval.append(Dependency(depender, package=package))

		return retval



class Package(db.Model):
	id           = db.Column(db.Integer, primary_key=True)

	# Basic details
	author_id    = db.Column(db.Integer, db.ForeignKey("user.id"))
	name         = db.Column(db.String(100), nullable=False)
	title        = db.Column(db.String(100), nullable=False)
	shortDesc    = db.Column(db.String(200), nullable=False)
	desc         = db.Column(db.Text, nullable=True)
	type         = db.Column(db.Enum(PackageType))
	created_at   = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

	license_id   = db.Column(db.Integer, db.ForeignKey("license.id"), nullable=False, default=1)
	license      = db.relationship("License", foreign_keys=[license_id])
	media_license_id = db.Column(db.Integer, db.ForeignKey("license.id"), nullable=False, default=1)
	media_license    = db.relationship("License", foreign_keys=[media_license_id])

	approved     = db.Column(db.Boolean, nullable=False, default=False)
	soft_deleted = db.Column(db.Boolean, nullable=False, default=False)

	score        = db.Column(db.Float, nullable=False, default=0)

	review_thread_id = db.Column(db.Integer, db.ForeignKey("thread.id"), nullable=True, default=None)
	review_thread    = db.relationship("Thread", foreign_keys=[review_thread_id])

	# Downloads
	repo         = db.Column(db.String(200), nullable=True)
	website      = db.Column(db.String(200), nullable=True)
	issueTracker = db.Column(db.String(200), nullable=True)
	forums       = db.Column(db.Integer,     nullable=True)

	provides = db.relationship("MetaPackage", secondary=provides, lazy="subquery",
			backref=db.backref("packages", lazy="dynamic"))

	dependencies = db.relationship("Dependency", backref="depender", lazy="dynamic", foreign_keys=[Dependency.depender_id])

	tags = db.relationship("Tag", secondary=tags, lazy="subquery",
			backref=db.backref("packages", lazy=True))

	releases = db.relationship("PackageRelease", backref="package",
			lazy="dynamic", order_by=db.desc("package_release_releaseDate"))

	screenshots = db.relationship("PackageScreenshot", backref="package",
			lazy="dynamic", order_by=db.asc("package_screenshot_id"))

	requests = db.relationship("EditRequest", backref="package",
			lazy="dynamic")

	def __init__(self, package=None):
		if package is None:
			return

		self.author_id = package.author_id
		self.created_at = package.created_at
		self.approved = package.approved

		for e in PackagePropertyKey:
			setattr(self, e.name, getattr(package, e.name))

	def getAsDictionaryShort(self, base_url, protonum=None):
		tnurl = self.getThumbnailURL(1)
		return {
			"name": self.name,
			"title": self.title,
			"author": self.author.display_name,
			"short_description": self.shortDesc,
			"type": self.type.toName(),
			"release": self.getDownloadRelease(protonum).id if self.getDownloadRelease(protonum) is not None else None,
			"thumbnail": (base_url + tnurl) if tnurl is not None else None,
			"score": round(self.score * 10) / 10
		}

	def getAsDictionary(self, base_url, protonum=None):
		tnurl = self.getThumbnailURL(1)
		return {
			"author": self.author.display_name,
			"name": self.name,
			"title": self.title,
			"short_description": self.shortDesc,
			"desc": self.desc,
			"type": self.type.toName(),
			"created_at": self.created_at,

			"license": self.license.name,
			"media_license": self.media_license.name,

			"repo": self.repo,
			"website": self.website,
			"issue_tracker": self.issueTracker,
			"forums": self.forums,

			"provides": [x.name for x in self.provides],
			"thumbnail": (base_url + tnurl) if tnurl is not None else None,
			"screenshots": [base_url + ss.url for ss in self.screenshots],

			"url": base_url + self.getDownloadURL(),
			"release": self.getDownloadRelease(protonum).id if self.getDownloadRelease(protonum) is not None else None,

			"score": round(self.score * 10) / 10
		}

	def getThumbnailURL(self, level=2):
		screenshot = self.screenshots.filter_by(approved=True).order_by(db.asc(PackageScreenshot.id)).first()
		return screenshot.getThumbnailURL(level) if screenshot is not None else None

	def getMainScreenshotURL(self):
		screenshot = self.screenshots.filter_by(approved=True).order_by(db.asc(PackageScreenshot.id)).first()
		return screenshot.url if screenshot is not None else None

	def getDetailsURL(self):
		return url_for("package_page",
				author=self.author.username, name=self.name)

	def getEditURL(self):
		return url_for("create_edit_package_page",
				author=self.author.username, name=self.name)

	def getApproveURL(self):
		return url_for("approve_package_page",
				author=self.author.username, name=self.name)

	def getRemoveURL(self):
		return url_for("remove_package_page",
				author=self.author.username, name=self.name)

	def getNewScreenshotURL(self):
		return url_for("create_screenshot_page",
				author=self.author.username, name=self.name)

	def getCreateReleaseURL(self):
		return url_for("create_release_page",
				author=self.author.username, name=self.name)

	def getCreateEditRequestURL(self):
		return url_for("create_edit_editrequest_page",
				author=self.author.username, name=self.name)

	def getBulkReleaseURL(self):
		return url_for("bulk_change_release_page",
			author=self.author.username, name=self.name)

	def getDownloadURL(self):
		return url_for("package_download_page",
				author=self.author.username, name=self.name)

	def getDownloadRelease(self, protonum=None):
		version = None
		if protonum is not None:
			version = MinetestRelease.query.filter(MinetestRelease.protocol >= int(protonum)).first()
			if version is not None:
				version = version.id
			else:
				version = 10000000


		for rel in self.releases:
			if rel.approved and (protonum is None or
					((rel.min_rel is None or rel.min_rel_id <= version) and \
					(rel.max_rel is None or rel.max_rel_id >= version))):
				return rel

		return None

	def getDownloadCount(self):
		counter = 0
		for release in self.releases:
			counter += release.downloads
		return counter

	def checkPerm(self, user, perm):
		if not user.is_authenticated:
			return False

		if type(perm) == str:
			perm = Permission[perm]
		elif type(perm) != Permission:
			raise Exception("Unknown permission given to Package.checkPerm()")

		isOwner = user == self.author

		if perm == Permission.CREATE_THREAD:
			return user.rank.atLeast(UserRank.MEMBER)

		# Members can edit their own packages, and editors can edit any packages
		if perm == Permission.MAKE_RELEASE or perm == Permission.ADD_SCREENSHOTS:
			return isOwner or user.rank.atLeast(UserRank.EDITOR)

		if perm == Permission.EDIT_PACKAGE or perm == Permission.APPROVE_CHANGES:
			if isOwner:
				return user.rank.atLeast(UserRank.MEMBER if self.approved else UserRank.NEW_MEMBER)
			else:
				return user.rank.atLeast(UserRank.EDITOR)

		# Editors can change authors and approve new packages
		elif perm == Permission.APPROVE_NEW or perm == Permission.CHANGE_AUTHOR:
			return user.rank.atLeast(UserRank.EDITOR)

		elif perm == Permission.APPROVE_RELEASE or perm == Permission.APPROVE_SCREENSHOT:
			return user.rank.atLeast(UserRank.TRUSTED_MEMBER if isOwner else UserRank.EDITOR)

		# Moderators can delete packages
		elif perm == Permission.DELETE_PACKAGE or perm == Permission.UNAPPROVE_PACKAGE \
				or perm == Permission.CHANGE_RELEASE_URL:
			return user.rank.atLeast(UserRank.MODERATOR)

		else:
			raise Exception("Permission {} is not related to packages".format(perm.name))

	def recalcScore(self):
		self.score = 10

		if self.forums is not None:
			topic = ForumTopic.query.get(self.forums)
			if topic:
				days   = (datetime.datetime.now() - topic.created_at).days
				months = days / 30
				years  = days / 365
				self.score = topic.views / max(years, 0.0416) + 80*min(max(months, 0.5), 6)

		if self.getMainScreenshotURL() is None:
			self.score *= 0.8

		if not self.license.is_foss or not self.media_license.is_foss:
			self.score *= 0.1

class MetaPackage(db.Model):
	id           = db.Column(db.Integer, primary_key=True)
	name         = db.Column(db.String(100), unique=True, nullable=False)
	dependencies = db.relationship("Dependency", backref="meta_package", lazy="dynamic")

	def __init__(self, name=None):
		self.name = name

	def __str__(self):
		return self.name

	@staticmethod
	def ListToSpec(list):
		return ",".join([str(x) for x in list])

	@staticmethod
	def GetOrCreate(name, cache={}):
		mp = cache.get(name)
		if mp is None:
			mp = MetaPackage.query.filter_by(name=name).first()

		if mp is None:
			mp = MetaPackage(name)
			db.session.add(mp)

		cache[name] = mp
		return mp

	@staticmethod
	def SpecToList(spec, cache={}):
		retval = []
		arr = spec.split(",")

		import re
		pattern = re.compile("^([a-z0-9_]+)$")

		for x in arr:
			x = x.strip()
			if x == "":
				continue

			if not pattern.match(x):
				continue

			retval.append(MetaPackage.GetOrCreate(x, cache))

		return retval

class Tag(db.Model):
	id              = db.Column(db.Integer,    primary_key=True)
	name            = db.Column(db.String(100), unique=True, nullable=False)
	title           = db.Column(db.String(100), nullable=False)
	backgroundColor = db.Column(db.String(6),   nullable=False)
	textColor       = db.Column(db.String(6),   nullable=False)

	def __init__(self, title, backgroundColor="000000", textColor="ffffff"):
		self.title           = title
		self.backgroundColor = backgroundColor
		self.textColor       = textColor

		import re
		regex = re.compile("[^a-z_]")
		self.name = regex.sub("", self.title.lower().replace(" ", "_"))


class MinetestRelease(db.Model):
	id       = db.Column(db.Integer, primary_key=True)
	name     = db.Column(db.String(100), unique=True, nullable=False)
	protocol = db.Column(db.Integer, nullable=False, default=0)

	def __init__(self, name=None):
		self.name = name

	def getActual(self):
		return None if self.name == "None" else self


class PackageRelease(db.Model):
	id           = db.Column(db.Integer, primary_key=True)

	package_id   = db.Column(db.Integer, db.ForeignKey("package.id"))
	title        = db.Column(db.String(100), nullable=False)
	releaseDate  = db.Column(db.DateTime,    nullable=False)
	url          = db.Column(db.String(200), nullable=False)
	approved     = db.Column(db.Boolean, nullable=False, default=False)
	task_id      = db.Column(db.String(37), nullable=True)
	commit_hash  = db.Column(db.String(41), nullable=True, default=None)
	downloads    = db.Column(db.Integer, nullable=False, default=0)

	min_rel_id = db.Column(db.Integer, db.ForeignKey("minetest_release.id"), nullable=True, server_default=None)
	min_rel    = db.relationship("MinetestRelease", foreign_keys=[min_rel_id])

	max_rel_id = db.Column(db.Integer, db.ForeignKey("minetest_release.id"), nullable=True, server_default=None)
	max_rel    = db.relationship("MinetestRelease", foreign_keys=[max_rel_id])


	def getEditURL(self):
		return url_for("edit_release_page",
				author=self.package.author.username,
				name=self.package.name,
				id=self.id)

	def getDownloadURL(self):
		return url_for("download_release_page",
				author=self.package.author.username,
				name=self.package.name,
				id=self.id)


	def __init__(self):
		self.releaseDate = datetime.datetime.now()


class PackageReview(db.Model):
	id         = db.Column(db.Integer, primary_key=True)
	package_id = db.Column(db.Integer, db.ForeignKey("package.id"))
	thread_id  = db.Column(db.Integer, db.ForeignKey("thread.id"), nullable=False)
	recommend  = db.Column(db.Boolean, nullable=False, default=True)


class PackageScreenshot(db.Model):
	id         = db.Column(db.Integer, primary_key=True)
	package_id = db.Column(db.Integer, db.ForeignKey("package.id"))
	title      = db.Column(db.String(100), nullable=False)
	url        = db.Column(db.String(100), nullable=False)
	approved   = db.Column(db.Boolean, nullable=False, default=False)


	def getEditURL(self):
		return url_for("edit_screenshot_page",
				author=self.package.author.username,
				name=self.package.name,
				id=self.id)

	def getThumbnailURL(self, level=2):
		return self.url.replace("/uploads/", ("/thumbnails/{:d}/").format(level))



class EditRequest(db.Model):
	id           = db.Column(db.Integer, primary_key=True)

	package_id   = db.Column(db.Integer, db.ForeignKey("package.id"))
	author_id    = db.Column(db.Integer, db.ForeignKey("user.id"))

	title        = db.Column(db.String(100), nullable=False)
	desc         = db.Column(db.String(1000), nullable=True)

	# 0 - open
	# 1 - merged
	# 2 - rejected
	status       = db.Column(db.Integer, nullable=False, default=0)

	changes = db.relationship("EditRequestChange", backref="request",
			lazy="dynamic")

	def getURL(self):
		return url_for("view_editrequest_page",
				author=self.package.author.username,
				name=self.package.name,
				id=self.id)

	def getApproveURL(self):
		return url_for("approve_editrequest_page",
				author=self.package.author.username,
				name=self.package.name,
				id=self.id)

	def getRejectURL(self):
		return url_for("reject_editrequest_page",
				author=self.package.author.username,
				name=self.package.name,
				id=self.id)

	def getEditURL(self):
		return url_for("create_edit_editrequest_page",
				author=self.package.author.username,
				name=self.package.name,
				id=self.id)

	def applyAll(self, package):
		for change in self.changes:
			change.apply(package)


	def checkPerm(self, user, perm):
		if not user.is_authenticated:
			return False

		if type(perm) == str:
			perm = Permission[perm]
		elif type(perm) != Permission:
			raise Exception("Unknown permission given to EditRequest.checkPerm()")

		isOwner = user == self.author

		# Members can edit their own packages, and editors can edit any packages
		if perm == Permission.EDIT_EDITREQUEST:
			return isOwner or user.rank.atLeast(UserRank.EDITOR)

		else:
			raise Exception("Permission {} is not related to packages".format(perm.name))




class EditRequestChange(db.Model):
	id           = db.Column(db.Integer, primary_key=True)

	request_id   = db.Column(db.Integer, db.ForeignKey("edit_request.id"))
	key          = db.Column(db.Enum(PackagePropertyKey), nullable=False)

	# TODO: make diff instead
	oldValue     = db.Column(db.Text, nullable=True)
	newValue     = db.Column(db.Text, nullable=True)

	def apply(self, package):
		if self.key == PackagePropertyKey.tags:
			package.tags.clear()
			for tagTitle in self.newValue.split(","):
				tag = Tag.query.filter_by(title=tagTitle.strip()).first()
				package.tags.append(tag)

		else:
			setattr(package, self.key.name, self.newValue)


watchers = db.Table("watchers",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("thread_id", db.Integer, db.ForeignKey("thread.id"), primary_key=True)
)

class Thread(db.Model):
	id         = db.Column(db.Integer, primary_key=True)

	package_id = db.Column(db.Integer, db.ForeignKey("package.id"), nullable=True)
	package    = db.relationship("Package", foreign_keys=[package_id])

	author_id  = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
	title      = db.Column(db.String(100), nullable=False)
	private    = db.Column(db.Boolean, server_default="0")

	created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

	replies    = db.relationship("ThreadReply", backref="thread", lazy="dynamic")

	watchers   = db.relationship("User", secondary=watchers, lazy="subquery", \
						backref=db.backref("watching", lazy=True))


	def getSubscribeURL(self):
		return url_for("thread_subscribe_page",
				id=self.id)

	def getUnsubscribeURL(self):
		return url_for("thread_unsubscribe_page",
				id=self.id)

	def checkPerm(self, user, perm):
		if not user.is_authenticated:
			return not self.private

		if type(perm) == str:
			perm = Permission[perm]
		elif type(perm) != Permission:
			raise Exception("Unknown permission given to Thread.checkPerm()")

		isOwner = user == self.author or (self.package is not None and self.package.author == user)

		if perm == Permission.SEE_THREAD:
			return not self.private or isOwner or user.rank.atLeast(UserRank.EDITOR)

		else:
			raise Exception("Permission {} is not related to threads".format(perm.name))

class ThreadReply(db.Model):
	id         = db.Column(db.Integer, primary_key=True)
	thread_id  = db.Column(db.Integer, db.ForeignKey("thread.id"), nullable=False)
	comment    = db.Column(db.String(500), nullable=False)
	author_id  = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
	created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)


REPO_BLACKLIST = [".zip", "mediafire.com", "dropbox.com", "weebly.com", \
		"minetest.net", "dropboxusercontent.com", "4shared.com", \
		"digitalaudioconcepts.com", "hg.intevation.org", "www.wtfpl.net", \
		"imageshack.com", "imgur.com"]

class ForumTopic(db.Model):
	topic_id  = db.Column(db.Integer, primary_key=True, autoincrement=False)
	author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
	author    = db.relationship("User")

	wip       = db.Column(db.Boolean, server_default="0")
	discarded = db.Column(db.Boolean, server_default="0")

	type      = db.Column(db.Enum(PackageType), nullable=False)
	title     = db.Column(db.String(200), nullable=False)
	name      = db.Column(db.String(30), nullable=True)
	link      = db.Column(db.String(200), nullable=True)

	posts     = db.Column(db.Integer, nullable=False)
	views     = db.Column(db.Integer, nullable=False)

	created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

	def getRepoURL(self):
		if self.link is None:
			return None

		for item in REPO_BLACKLIST:
			if item in self.link:
				return None

		return self.link.replace("repo.or.cz/w/", "repo.or.cz/")

	def getAsDictionary(self):
		return {
			"author": self.author.username,
			"name":   self.name,
			"type":   self.type.toName(),
			"title":  self.title,
			"id":     self.topic_id,
			"link":   self.link,
			"posts":  self.posts,
			"views":  self.views,
			"is_wip": self.wip,
			"discarded":  self.discarded,
			"created_at": self.created_at.isoformat(),
		}

	def checkPerm(self, user, perm):
		if not user.is_authenticated:
			return False

		if type(perm) == str:
			perm = Permission[perm]
		elif type(perm) != Permission:
			raise Exception("Unknown permission given to ForumTopic.checkPerm()")

		if perm == Permission.TOPIC_DISCARD:
			return self.author == user or user.rank.atLeast(UserRank.EDITOR)

		else:
			raise Exception("Permission {} is not related to topics".format(perm.name))


# Setup Flask-User
db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
user_manager = UserManager(db_adapter, app)     # Initialize Flask-User
