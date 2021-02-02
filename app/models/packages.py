# ContentDB
# Copyright (C) 2018-21  rubenwardy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import datetime
import enum

from flask import url_for
from flask_sqlalchemy import BaseQuery
from sqlalchemy_searchable import SearchQueryMixin
from sqlalchemy_utils.types import TSVectorType

from . import db
from .users import Permission, UserRank, User


class PackageQuery(BaseQuery, SearchQueryMixin):
	pass


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


class PackageState(enum.Enum):
	WIP = "Draft"
	CHANGES_NEEDED  = "Changes Needed"
	READY_FOR_REVIEW = "Ready for Review"
	APPROVED = "Approved"
	DELETED = "Deleted"

	def toName(self):
		return self.name.lower()

	def verb(self):
		if self == self.READY_FOR_REVIEW:
			return "Submit for Review"
		elif self == self.APPROVED:
			return "Approve"
		elif self == self.DELETED:
			return "Delete"
		else:
			return self.value

	def __str__(self):
		return self.name

	@classmethod
	def get(cls, name):
		try:
			return PackageState[name.upper()]
		except KeyError:
			return None

	@classmethod
	def choices(cls):
		return [(choice, choice.value) for choice in cls]

	@classmethod
	def coerce(cls, item):
		return item if type(item) == PackageState else PackageState[item]


PACKAGE_STATE_FLOW = {
	PackageState.WIP: {PackageState.READY_FOR_REVIEW},
	PackageState.CHANGES_NEEDED: {PackageState.READY_FOR_REVIEW},
	PackageState.READY_FOR_REVIEW: {PackageState.WIP, PackageState.CHANGES_NEEDED, PackageState.APPROVED},
	PackageState.APPROVED: {PackageState.CHANGES_NEEDED},
	PackageState.DELETED: {PackageState.READY_FOR_REVIEW},
}


class PackagePropertyKey(enum.Enum):
	name          = "Name"
	title         = "Title"
	short_desc     = "Short Description"
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


Tags = db.Table("tags",
	db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
	db.Column("package_id", db.Integer, db.ForeignKey("package.id"), primary_key=True)
)


ContentWarnings = db.Table("content_warnings",
	db.Column("content_warning_id", db.Integer, db.ForeignKey("content_warning.id"), primary_key=True),
	db.Column("package_id", db.Integer, db.ForeignKey("package.id"), primary_key=True)
)


maintainers = db.Table("maintainers",
	db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
	db.Column("package_id", db.Integer, db.ForeignKey("package.id"), primary_key=True)
)


class Dependency(db.Model):
	id              = db.Column(db.Integer, primary_key=True)

	depender_id     = db.Column(db.Integer, db.ForeignKey("package.id"),     nullable=True)
	depender        = db.relationship("Package", foreign_keys=[depender_id])

	package_id      = db.Column(db.Integer, db.ForeignKey("package.id"),     nullable=True)
	package         = db.relationship("Package", foreign_keys=[package_id])

	meta_package_id = db.Column(db.Integer, db.ForeignKey("meta_package.id"), nullable=True)
	meta_package = db.relationship("MetaPackage", foreign_keys=[meta_package_id])

	optional        = db.Column(db.Boolean, nullable=False, default=False)

	__table_args__  = (db.UniqueConstraint("depender_id", "package_id", "meta_package_id", name="_dependency_uc"), )

	def __init__(self, depender=None, package=None, meta=None, optional=False):
		if depender is None:
			return

		self.depender = depender
		self.optional = optional

		packageProvided = package is not None
		metaProvided = meta is not None

		if packageProvided and not metaProvided:
			self.package = package
		elif metaProvided and not packageProvided:
			self.meta_package = meta
		else:
			raise Exception("Either meta or package must be given, but not both!")

	def getName(self):
		if self.meta_package:
			return self.meta_package.name
		elif self.package:
			return self.package.name
		else:
			assert False

	def __str__(self):
		if self.package is not None:
			return self.package.author.username + "/" + self.package.name
		elif self.meta_package is not None:
			return self.meta_package.name
		else:
			raise Exception("Meta and package are both none!")

	@staticmethod
	def SpecToList(depender, spec, cache):
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
	query_class  = PackageQuery

	id           = db.Column(db.Integer, primary_key=True)

	# Basic details
	author_id    = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
	author       = db.relationship("User", back_populates="packages", foreign_keys=[author_id])

	name         = db.Column(db.Unicode(100), nullable=False)
	title        = db.Column(db.Unicode(100), nullable=False)
	short_desc   = db.Column(db.Unicode(200), nullable=False)
	desc         = db.Column(db.UnicodeText, nullable=True)
	type         = db.Column(db.Enum(PackageType), nullable=False)
	created_at   = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
	approved_at  = db.Column(db.DateTime, nullable=True, default=None)

	name_valid = db.CheckConstraint("name ~* '^[a-z0-9_]+$'")

	search_vector = db.Column(TSVectorType("name", "title", "short_desc", "desc",
			weights={ "name": "A", "title": "B", "short_desc": "C", "desc": "D" }))

	license_id   = db.Column(db.Integer, db.ForeignKey("license.id"), nullable=False, default=1)
	license      = db.relationship("License", foreign_keys=[license_id])
	media_license_id = db.Column(db.Integer, db.ForeignKey("license.id"), nullable=False, default=1)
	media_license    = db.relationship("License", foreign_keys=[media_license_id])

	state         = db.Column(db.Enum(PackageState), nullable=False, default=PackageState.WIP)

	@property
	def approved(self):
		return self.state == PackageState.APPROVED

	score        = db.Column(db.Float, nullable=False, default=0)
	score_downloads = db.Column(db.Float, nullable=False, default=0)
	downloads     = db.Column(db.Integer, nullable=False, default=0)

	review_thread_id = db.Column(db.Integer, db.ForeignKey("thread.id"), nullable=True, default=None)
	review_thread    = db.relationship("Thread", uselist=False, foreign_keys=[review_thread_id], back_populates="is_review_thread")

	# Downloads
	repo         = db.Column(db.String(200), nullable=True)
	website      = db.Column(db.String(200), nullable=True)
	issueTracker = db.Column(db.String(200), nullable=True)
	forums       = db.Column(db.Integer,     nullable=True)

	provides = db.relationship("MetaPackage", secondary=provides, order_by=db.asc("name"), back_populates="packages")

	dependencies = db.relationship("Dependency", back_populates="depender", lazy="dynamic", foreign_keys=[Dependency.depender_id])

	tags = db.relationship("Tag", secondary=Tags, back_populates="packages")

	content_warnings = db.relationship("ContentWarning", secondary=ContentWarnings, back_populates="packages")

	releases = db.relationship("PackageRelease", back_populates="package",
			lazy="dynamic", order_by=db.desc("package_release_releaseDate"), cascade="all, delete, delete-orphan")

	screenshots = db.relationship("PackageScreenshot", back_populates="package", foreign_keys="PackageScreenshot.package_id",
			lazy="dynamic", order_by=db.asc("package_screenshot_order"), cascade="all, delete, delete-orphan")

	main_screenshot = db.relationship("PackageScreenshot", uselist=False, foreign_keys="PackageScreenshot.package_id",
			lazy=True, order_by=db.asc("package_screenshot_order"),
			primaryjoin="and_(Package.id==PackageScreenshot.package_id, PackageScreenshot.approved)")

	cover_image_id = db.Column(db.Integer, db.ForeignKey("package_screenshot.id"), nullable=True, default=None)
	cover_image = db.relationship("PackageScreenshot", uselist=False, foreign_keys=[cover_image_id])

	maintainers = db.relationship("User", secondary=maintainers)

	threads = db.relationship("Thread", back_populates="package", order_by=db.desc("thread_created_at"),
			foreign_keys="Thread.package_id", cascade="all, delete, delete-orphan", lazy="dynamic")

	reviews = db.relationship("PackageReview", back_populates="package", order_by=db.desc("package_review_created_at"),
			cascade="all, delete, delete-orphan")

	audit_log_entries = db.relationship("AuditLogEntry", foreign_keys="AuditLogEntry.package_id", back_populates="package",
			order_by=db.desc("audit_log_entry_created_at"))

	notifications = db.relationship("Notification", foreign_keys="Notification.package_id",
			back_populates="package", cascade="all, delete, delete-orphan")

	tokens = db.relationship("APIToken", foreign_keys="APIToken.package_id", back_populates="package",
			cascade="all, delete, delete-orphan")

	update_config = db.relationship("PackageUpdateConfig", uselist=False, back_populates="package",
			cascade="all, delete, delete-orphan")

	def __init__(self, package=None):
		if package is None:
			return

		self.author_id = package.author_id
		self.created_at = package.created_at
		self.state = package.state

		self.maintainers.append(self.author)

		for e in PackagePropertyKey:
			setattr(self, e.name, getattr(package, e.name))

	def getId(self):
		return "{}/{}".format(self.author.username, self.name)

	def getIsFOSS(self):
		return self.license.is_foss and self.media_license.is_foss

	def getSortedDependencies(self, is_hard=None):
		query = self.dependencies
		if is_hard is not None:
			query = query.filter_by(optional=not is_hard)

		deps = query.all()
		deps.sort(key = lambda x: x.getName())
		return deps

	def getSortedHardDependencies(self):
		return self.getSortedDependencies(True)

	def getSortedOptionalDependencies(self):
		return self.getSortedDependencies(False)

	def getAsDictionaryKey(self):
		return {
			"name": self.name,
			"author": self.author.display_name,
			"type": self.type.toName(),
		}

	def getAsDictionaryShort(self, base_url, version=None, release_id=None, no_load=False):
		tnurl = self.getThumbnailURL(1)

		if release_id is None and no_load == False:
			release = self.getDownloadRelease(version=version)
			release_id = release and release.id

		return {
			"name": self.name,
			"title": self.title,
			"author": self.author.username,
			"short_description": self.short_desc,
			"type": self.type.toName(),
			"release": release_id,
			"thumbnail": (base_url + tnurl) if tnurl is not None else None
		}

	def getAsDictionary(self, base_url, version=None):
		tnurl = self.getThumbnailURL(1)
		release = self.getDownloadRelease(version=version)
		return {
			"author": self.author.username,
			"name": self.name,
			"title": self.title,
			"short_description": self.short_desc,
			"desc": self.desc,
			"type": self.type.toName(),
			"created_at": self.created_at.isoformat(),

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
			"release": release and release.id,

			"score": round(self.score * 10) / 10,
			"downloads": self.downloads
		}

	def getThumbnailOrPlaceholder(self, level=2):
		return self.getThumbnailURL(level) or "/static/placeholder.png"

	def getThumbnailURL(self, level=2):
		screenshot = self.main_screenshot
		return screenshot.getThumbnailURL(level) if screenshot is not None else None

	def getMainScreenshotURL(self, absolute=False):
		screenshot = self.main_screenshot
		if screenshot is None:
			return None

		if absolute:
			from app.utils import abs_url
			return abs_url(screenshot.url)
		else:
			return screenshot.url

	def getDetailsURL(self, absolute=False):
		if absolute:
			from app.utils import abs_url_for
			return abs_url_for("packages.view",
					author=self.author.username, name=self.name)
		else:
			return url_for("packages.view",
					author=self.author.username, name=self.name)

	def getShieldURL(self, type):
		from app.utils import abs_url_for
		return abs_url_for("packages.shield",
				author=self.author.username, name=self.name, type=type)

	def makeShield(self, type):
		return "[![ContentDB]({})]({})" \
			.format(self.getShieldURL(type), self.getDetailsURL(True))

	def getEditURL(self):
		return url_for("packages.create_edit",
				author=self.author.username, name=self.name)

	def getSetStateURL(self, state):
		if type(state) == str:
			state = PackageState[state]
		elif type(state) != PackageState:
			raise Exception("Unknown state given to Package.canMoveToState()")

		return url_for("packages.move_to_state",
				author=self.author.username, name=self.name, state=state.name.lower())

	def getRemoveURL(self):
		return url_for("packages.remove",
				author=self.author.username, name=self.name)

	def getNewScreenshotURL(self):
		return url_for("packages.create_screenshot",
				author=self.author.username, name=self.name)

	def getEditScreenshotsURL(self):
		return url_for("packages.screenshots",
				author=self.author.username, name=self.name)

	def getCreateReleaseURL(self, **kwargs):
		return url_for("packages.create_release",
				author=self.author.username, name=self.name, **kwargs)

	def getBulkReleaseURL(self):
		return url_for("packages.bulk_change_release",
			author=self.author.username, name=self.name)

	def getUpdateConfigURL(self, action=None):
		return url_for("packages.update_config",
			author=self.author.username, name=self.name, action=action)

	def getSetupReleasesURL(self):
		return url_for("packages.setup_releases",
			author=self.author.username, name=self.name)

	def getDownloadURL(self):
		return url_for("packages.download",
				author=self.author.username, name=self.name)

	def getEditMaintainersURL(self):
		return url_for("packages.edit_maintainers",
				author=self.author.username, name=self.name)

	def getRemoveSelfMaintainerURL(self):
		return url_for("packages.remove_self_maintainers",
				author=self.author.username, name=self.name)

	def getUpdateFromReleaseURL(self):
		return url_for("packages.update_from_release",
				author=self.author.username, name=self.name)

	def getReviewURL(self):
		return url_for('packages.review',
				author=self.author.username, name=self.name)

	def getDownloadRelease(self, version=None):
		for rel in self.releases:
			if rel.approved and (version is None or
					((rel.min_rel is None or rel.min_rel_id <= version.id) and
					 (rel.max_rel is None or rel.max_rel_id >= version.id))):
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
		isMaintainer = isOwner or user.rank.atLeast(UserRank.EDITOR) or user in self.maintainers

		if perm == Permission.CREATE_THREAD:
			return user.rank.atLeast(UserRank.MEMBER)

		# Members can edit their own packages, and editors can edit any packages
		elif perm == Permission.MAKE_RELEASE or perm == Permission.ADD_SCREENSHOTS:
			return isMaintainer

		elif perm == Permission.EDIT_PACKAGE or \
				perm == Permission.APPROVE_CHANGES or perm == Permission.APPROVE_RELEASE:
			return isMaintainer and user.rank.atLeast(UserRank.MEMBER if self.approved else UserRank.NEW_MEMBER)

		# Anyone can change the package name when not approved, but only editors when approved
		elif perm == Permission.CHANGE_NAME:
			return not self.approved or user.rank.atLeast(UserRank.EDITOR)

		# Editors can change authors and approve new packages
		elif perm == Permission.APPROVE_NEW or perm == Permission.CHANGE_AUTHOR:
			return user.rank.atLeast(UserRank.EDITOR)

		elif perm == Permission.APPROVE_SCREENSHOT:
			return isMaintainer and user.rank.atLeast(UserRank.TRUSTED_MEMBER if self.approved else UserRank.NEW_MEMBER)

		elif perm == Permission.EDIT_MAINTAINERS:
			return isOwner or user.rank.atLeast(UserRank.MODERATOR)

		elif perm == Permission.UNAPPROVE_PACKAGE or perm == Permission.DELETE_PACKAGE:
			return user.rank.atLeast(UserRank.MEMBER if isOwner else UserRank.EDITOR)

		elif perm == Permission.CHANGE_RELEASE_URL:
			return user.rank.atLeast(UserRank.MODERATOR)

		elif perm == Permission.REIMPORT_META:
			return user.rank.atLeast(UserRank.ADMIN)

		else:
			raise Exception("Permission {} is not related to packages".format(perm.name))

	def getMissingHardDependenciesQuery(self):
		return MetaPackage.query \
			.filter(~ MetaPackage.packages.any(state=PackageState.APPROVED)) \
			.filter(MetaPackage.dependencies.any(optional=False, depender=self)) \
			.order_by(db.asc(MetaPackage.name))

	def getMissingHardDependencies(self):
		return [mp.name for mp in self.getMissingHardDependenciesQuery().all()]

	def canMoveToState(self, user, state):
		if not user.is_authenticated:
			return False

		if type(state) == str:
			state = PackageState[state]
		elif type(state) != PackageState:
			raise Exception("Unknown state given to Package.canMoveToState()")

		if state not in PACKAGE_STATE_FLOW[self.state]:
			return False

		if state == PackageState.READY_FOR_REVIEW or state == PackageState.APPROVED:
			requiredPerm = Permission.APPROVE_NEW if state == PackageState.APPROVED else Permission.EDIT_PACKAGE

			if not self.checkPerm(user, requiredPerm):
				return False

			if state == PackageState.APPROVED and  ("Other" in self.license.name or "Other" in self.media_license.name):
				return False

			if self.getMissingHardDependenciesQuery().count() > 0:
				return False

			needsScreenshot = \
				(self.type == self.type.GAME or self.type == self.type.TXP) and \
					self.screenshots.count() == 0
			return self.releases.count() > 0 and not needsScreenshot

		elif state == PackageState.CHANGES_NEEDED:
			return self.checkPerm(user, Permission.APPROVE_NEW)

		elif state == PackageState.WIP:
			return self.checkPerm(user, Permission.EDIT_PACKAGE) and \
				(user in self.maintainers or user.rank.atLeast(UserRank.ADMIN))

		return True

	def getNextStates(self, user):
		states = []

		for state in PackageState:
			if self.canMoveToState(user, state):
				states.append(state)

		return states

	def getScoreDict(self):
		return {
			"author": self.author.username,
			"name": self.name,
			"score": self.score,
			"score_downloads": self.score_downloads,
			"score_reviews": self.score - self.score_downloads,
			"downloads": self.downloads
		}

	def recalcScore(self):
		review_scores = [ 100 * r.asSign() for r in self.reviews ]
		self.score = self.score_downloads + sum(review_scores)


class MetaPackage(db.Model):
	id           = db.Column(db.Integer, primary_key=True)
	name         = db.Column(db.String(100), unique=True, nullable=False)
	dependencies = db.relationship("Dependency", back_populates="meta_package", lazy="dynamic")
	packages     = db.relationship("Package", lazy="dynamic", back_populates="provides", secondary=provides)

	mp_name_valid = db.CheckConstraint("name ~* '^[a-z0-9_]+$'")

	def __init__(self, name=None):
		self.name = name

	def __str__(self):
		return self.name

	@staticmethod
	def ListToSpec(list):
		return ",".join([str(x) for x in list])

	@staticmethod
	def GetOrCreate(name, cache):
		mp = cache.get(name)
		if mp is None:
			mp = MetaPackage.query.filter_by(name=name).first()

		if mp is None:
			mp = MetaPackage(name)
			db.session.add(mp)

		cache[name] = mp
		return mp

	@staticmethod
	def SpecToList(spec, cache):
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


class ContentWarning(db.Model):
	id              = db.Column(db.Integer, primary_key=True)
	name            = db.Column(db.String(100), unique=True, nullable=False)
	title           = db.Column(db.String(100), nullable=False)
	description     = db.Column(db.String(500), nullable=False)

	packages        = db.relationship("Package", back_populates="content_warnings", secondary=ContentWarnings)

	def __init__(self, title, description=""):
		self.title       = title
		self.description = description

		import re
		regex = re.compile("[^a-z_]")
		self.name = regex.sub("", self.title.lower().replace(" ", "_"))


class Tag(db.Model):
	id              = db.Column(db.Integer, primary_key=True)
	name            = db.Column(db.String(100), unique=True, nullable=False)
	title           = db.Column(db.String(100), nullable=False)
	description     = db.Column(db.String(500), nullable=True, default=None)
	backgroundColor = db.Column(db.String(6), nullable=False)
	textColor       = db.Column(db.String(6), nullable=False)
	views           = db.Column(db.Integer, nullable=False, default=0)

	packages        = db.relationship("Package", back_populates="tags", secondary=Tags)

	def __init__(self, title, backgroundColor="000000", textColor="ffffff"):
		self.title           = title
		self.backgroundColor = backgroundColor
		self.textColor       = textColor

		import re
		regex = re.compile("[^a-z_]")
		self.name = regex.sub("", self.title.lower().replace(" ", "_"))

	def getAsDictionary(self):
		description = self.description if self.description != "" else None
		return { "name": self.name, "title": self.title, "description": description }


class MinetestRelease(db.Model):
	id       = db.Column(db.Integer, primary_key=True)
	name     = db.Column(db.String(100), unique=True, nullable=False)
	protocol = db.Column(db.Integer, nullable=False, default=0)

	def __init__(self, name=None, protocol=0):
		self.name = name
		self.protocol = protocol

	def getActual(self):
		return None if self.name == "None" else self

	def getAsDictionary(self):
		return {
			"name": self.name,
			"protocol_version": self.protocol,
			"is_dev": "-dev" in self.name,
		}

	@classmethod
	def get(cls, version, protocol_num):
		if version:
			parts = version.strip().split(".")
			if len(parts) >= 2:
				major_minor = parts[0] + "." + parts[1]
				query = MinetestRelease.query.filter(MinetestRelease.name.like("{}%".format(major_minor)))
				if protocol_num:
					query = query.filter_by(protocol=protocol_num)

				release = query.one_or_none()
				if release:
					return release

		if protocol_num:
			return MinetestRelease.query.filter_by(protocol=protocol_num).first()

		return None


class PackageRelease(db.Model):
	id           = db.Column(db.Integer, primary_key=True)

	package_id   = db.Column(db.Integer, db.ForeignKey("package.id"))
	package      = db.relationship("Package", back_populates="releases", foreign_keys=[package_id])

	title        = db.Column(db.String(100), nullable=False)
	releaseDate  = db.Column(db.DateTime,    nullable=False)
	url          = db.Column(db.String(200), nullable=False, default="")
	approved     = db.Column(db.Boolean, nullable=False, default=False)
	task_id      = db.Column(db.String(37), nullable=True)
	commit_hash  = db.Column(db.String(41), nullable=True, default=None)
	downloads    = db.Column(db.Integer, nullable=False, default=0)

	min_rel_id = db.Column(db.Integer, db.ForeignKey("minetest_release.id"), nullable=True, server_default=None)
	min_rel    = db.relationship("MinetestRelease", foreign_keys=[min_rel_id])

	max_rel_id = db.Column(db.Integer, db.ForeignKey("minetest_release.id"), nullable=True, server_default=None)
	max_rel    = db.relationship("MinetestRelease", foreign_keys=[max_rel_id])

	# If the release is approved, then the task_id must be null and the url must be present
	CK_approval_valid = db.CheckConstraint("not approved OR (task_id IS NULL AND (url = '') IS NOT FALSE)")

	def getAsDictionary(self):
		return {
			"id": self.id,
			"title": self.title,
			"url": self.url if self.url != "" else None,
			"release_date": self.releaseDate.isoformat(),
			"commit": self.commit_hash,
			"downloads": self.downloads,
			"min_minetest_version": self.min_rel and self.min_rel.getAsDictionary(),
			"max_minetest_version": self.max_rel and self.max_rel.getAsDictionary(),
		}

	def getEditURL(self):
		return url_for("packages.edit_release",
				author=self.package.author.username,
				name=self.package.name,
				id=self.id)

	def getDeleteURL(self):
		return url_for("packages.delete_release",
				author=self.package.author.username,
				name=self.package.name,
				id=self.id)

	def getDownloadURL(self):
		return url_for("packages.download_release",
				author=self.package.author.username,
				name=self.package.name,
				id=self.id)

	def __init__(self):
		self.releaseDate = datetime.datetime.now()

	def approve(self, user):
		if not self.package.checkPerm(user, Permission.APPROVE_RELEASE):
			return False

		if self.approved:
			return True

		assert self.task_id is None and self.url is not None and self.url != ""

		self.approved = True

		if self.package.update_config:
			self.package.update_config.outdated_at = None
			self.package.update_config.last_commit = self.commit_hash

		return True

	def checkPerm(self, user, perm):
		if not user.is_authenticated:
			return False

		if type(perm) == str:
			perm = Permission[perm]
		elif type(perm) != Permission:
			raise Exception("Unknown permission given to PackageRelease.checkPerm()")

		isOwner = user == self.package.author

		if perm == Permission.DELETE_RELEASE:
			if user.rank.atLeast(UserRank.ADMIN):
				return True

			if not (isOwner or user.rank.atLeast(UserRank.EDITOR)):
				return False

			if not self.package.approved or self.task_id is not None:
				return True

			count = PackageRelease.query \
					.filter_by(package_id=self.package_id) \
					.filter(PackageRelease.id > self.id) \
					.count()

			return count > 0
		else:
			raise Exception("Permission {} is not related to releases".format(perm.name))


class PackageScreenshot(db.Model):
	id         = db.Column(db.Integer, primary_key=True)

	package_id = db.Column(db.Integer, db.ForeignKey("package.id"), nullable=False)
	package    = db.relationship("Package", back_populates="screenshots", foreign_keys=[package_id])

	order      = db.Column(db.Integer, nullable=False, default=0)
	title      = db.Column(db.String(100), nullable=False)
	url        = db.Column(db.String(100), nullable=False)
	approved   = db.Column(db.Boolean, nullable=False, default=False)
	created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

	def getEditURL(self):
		return url_for("packages.edit_screenshot",
				author=self.package.author.username,
				name=self.package.name,
				id=self.id)

	def getDeleteURL(self):
		return url_for("packages.delete_screenshot",
				author=self.package.author.username,
				name=self.package.name,
				id=self.id)

	def getThumbnailURL(self, level=2):
		return self.url.replace("/uploads/", "/thumbnails/{:d}/".format(level))

	def getAsDictionary(self, base_url=""):
		return {
			"id": self.id,
			"order": self.order,
			"title": self.title,
			"url": base_url + self.url,
			"approved": self.approved,
			"created_at": self.created_at.isoformat(),
		}


class PackageUpdateTrigger(enum.Enum):
	COMMIT = "New Commit"
	TAG = "New Tag"

	def toName(self):
		return self.name.lower()

	def __str__(self):
		return self.name

	@classmethod
	def get(cls, name):
		try:
			return PackageUpdateTrigger[name.upper()]
		except KeyError:
			return None

	@classmethod
	def choices(cls):
		return [(choice, choice.value) for choice in cls]

	@classmethod
	def coerce(cls, item):
		return item if type(item) == PackageUpdateTrigger else PackageUpdateTrigger[item]


class PackageUpdateConfig(db.Model):
	package_id  = db.Column(db.Integer, db.ForeignKey("package.id"), primary_key=True)
	package     = db.relationship("Package", back_populates="update_config", foreign_keys=[package_id])

	last_commit = db.Column(db.String(41), nullable=True, default=None)
	last_tag    = db.Column(db.String(41), nullable=True, default=None)

	# Set to now when an outdated notification is sent. Set to None when a release is created
	outdated_at = db.Column(db.DateTime, nullable=True, default=None)

	trigger     = db.Column(db.Enum(PackageUpdateTrigger), nullable=False, default=PackageUpdateTrigger.COMMIT)
	ref         = db.Column(db.String(41), nullable=True, default=None)

	make_release = db.Column(db.Boolean, nullable=False, default=False)

	# Was this made using Add Update Configs in Admin?
	auto_created = db.Column(db.Boolean, nullable=False, default=False)

	def set_outdated(self):
		self.outdated_at = datetime.datetime.utcnow()

	def get_message(self):
		if self.trigger == PackageUpdateTrigger.COMMIT:
			msg = "New commit {} found on the Git repo.".format(self.last_commit[0:5])

			last_release = self.package.releases.first()
			if last_release and last_release.commit_hash:
				msg += " The last release was commit {}".format(last_release.commit_hash[0:5])

			return msg

		else:
			return "New tag {} found on the Git repo.".format(self.last_tag)

	def get_title(self):
		return self.last_tag or self.outdated_at.strftime("%Y-%m-%d")

	def get_ref(self):
		return self.last_tag or self.last_commit

	def get_create_release_url(self):
		return self.package.getCreateReleaseURL(title=self.get_title(), ref=self.get_ref())
