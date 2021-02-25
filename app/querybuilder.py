from flask import abort, current_app
from sqlalchemy import or_
from sqlalchemy.orm import subqueryload
from sqlalchemy.sql.expression import func

from .models import db, PackageType, Package, ForumTopic, License, MinetestRelease, PackageRelease, User, Tag, ContentWarning, PackageState
from .utils import isYes, get_int_or_abort


class QueryBuilder:
	title  = None
	types  = None
	search = None

	def __init__(self, args):
		title = "Packages"

		# Get request types
		types = args.getlist("type")
		types = [PackageType.get(tname) for tname in types]
		types = [type for type in types if type is not None]
		if len(types) > 0:
			title = ", ".join([type.value + "s" for type in types])

		# Get tags types
		tags = args.getlist("tag")
		tags = [Tag.query.filter_by(name=tname).first() for tname in tags]
		tags = [tag for tag in tags if tag is not None]

		# Hide
		hide_flags = args.getlist("hide")


		self.title  = title
		self.types  = types
		self.tags   = tags

		self.random = "random" in args
		self.lucky  = "lucky" in args
		self.limit  = 1 if self.lucky else None
		self.order_by  = args.get("sort")
		self.order_dir = args.get("order") or "desc"

		self.hide_nonfree = "nonfree" in hide_flags
		self.hide_flags = set(hide_flags)
		self.hide_flags.discard("nonfree")

		# Filters
		self.search = args.get("q")
		self.author = args.get("author")

		protocol_version = get_int_or_abort(args.get("protocol_version"))
		minetest_version = args.get("engine_version")
		if protocol_version or minetest_version:
			self.version = MinetestRelease.get(minetest_version, protocol_version)
		else:
			self.version = None

		self.show_discarded = isYes(args.get("show_discarded"))
		self.show_added = args.get("show_added")
		if self.show_added is not None:
			self.show_added = isYes(self.show_added)

		if self.search is not None and self.search.strip() == "":
			self.search = None

	def setSortIfNone(self, name, dir="desc"):
		if self.order_by is None:
			self.order_by = name
			self.order_dir = dir

	def getReleases(self):
		releases_query = db.session.query(PackageRelease.package_id, func.max(PackageRelease.id)) \
			.select_from(PackageRelease).filter(PackageRelease.approved) \
			.group_by(PackageRelease.package_id)

		if self.version:
			releases_query = releases_query \
				.filter(or_(PackageRelease.min_rel_id == None,
					PackageRelease.min_rel_id <= self.version.id)) \
				.filter(or_(PackageRelease.max_rel_id == None,
					PackageRelease.max_rel_id >= self.version.id))

		return releases_query.all()

	def convertToDictionary(self, packages):
		releases = {}
		for [package_id, release_id] in self.getReleases():
			releases[package_id] = release_id

		def toJson(package: Package):
			release_id = releases.get(package.id)
			return package.getAsDictionaryShort(current_app.config["BASE_URL"], release_id=release_id, no_load=True)

		return [toJson(pkg) for pkg in packages]

	def buildPackageQuery(self):
		if self.order_by == "last_release":
			query = db.session.query(Package).select_from(PackageRelease).join(Package) \
				.filter_by(state=PackageState.APPROVED)
		else:
			query = Package.query.filter_by(state=PackageState.APPROVED)

		query = query.options(subqueryload(Package.main_screenshot))

		query = self.orderPackageQuery(self.filterPackageQuery(query))

		if self.limit:
			query = query.limit(self.limit)

		return query

	def filterPackageQuery(self, query):
		if len(self.types) > 0:
			query = query.filter(Package.type.in_(self.types))

		if self.author:
			author = User.query.filter_by(username=self.author).first()
			if not author:
				abort(404)

			query = query.filter_by(author=author)

		for tag in self.tags:
			query = query.filter(Package.tags.any(Tag.id == tag.id))

		if "android_default" in self.hide_flags:
			query = query.filter(~ Package.content_warnings.any())
		else:
			for flag in self.hide_flags:
				warning = ContentWarning.query.filter_by(name=flag).first()
				if warning:
					query = query.filter(~ Package.content_warnings.any(ContentWarning.id == warning.id))

		if self.hide_nonfree:
			query = query.filter(Package.license.has(License.is_foss == True))
			query = query.filter(Package.media_license.has(License.is_foss == True))

		if self.version:
			query = query.join(Package.releases) \
				.filter(PackageRelease.approved == True) \
				.filter(or_(PackageRelease.min_rel_id == None,
					PackageRelease.min_rel_id <= self.version.id)) \
				.filter(or_(PackageRelease.max_rel_id == None,
					PackageRelease.max_rel_id >= self.version.id))

		return query

	def orderPackageQuery(self, query):
		if self.search:
			query = query.search(self.search, sort=self.order_by is None)

		if self.random:
			query = query.order_by(func.random())
			return query

		to_order = None
		if self.order_by is None and self.search:
			pass
		elif self.order_by is None or self.order_by == "score":
			to_order = Package.score
		elif self.order_by == "reviews":
			query = query.filter(Package.reviews.any())
			to_order = (Package.score - Package.score_downloads)
		elif self.order_by == "name":
			to_order = Package.name
		elif self.order_by == "title":
			to_order = Package.title
		elif self.order_by == "downloads":
			to_order = Package.downloads
		elif self.order_by == "created_at" or self.order_by == "date":
			to_order = Package.created_at
		elif self.order_by == "approved_at" or self.order_by == "date":
			to_order = Package.approved_at
		elif self.order_by == "last_release":
			to_order = PackageRelease.releaseDate
		else:
			abort(400)

		if to_order is not None:
			if self.order_dir == "asc":
				to_order = db.asc(to_order)
			elif self.order_dir == "desc":
				to_order = db.desc(to_order)
			else:
				abort(400)

			query = query.order_by(to_order)

		return query

	def buildTopicQuery(self, show_added=False):
		query = ForumTopic.query

		if not self.show_discarded:
			query = query.filter_by(discarded=False)

		show_added = self.show_added == True or (self.show_added is None and show_added)
		if not show_added:
			query = query.filter(~ db.exists().where(Package.forums==ForumTopic.topic_id))

		if self.order_by is None or self.order_by == "name":
			query = query.order_by(db.asc(ForumTopic.wip), db.asc(ForumTopic.name), db.asc(ForumTopic.title))
		elif self.order_by == "views":
			query = query.order_by(db.desc(ForumTopic.views))
		elif self.order_by == "created_at" or self.order_by == "date":
			query = query.order_by(db.asc(ForumTopic.created_at))

		if self.search:
			query = query.filter(or_(ForumTopic.title.ilike('%' + self.search + '%'),
					ForumTopic.name == self.search.lower()))

		if len(self.types) > 0:
			query = query.filter(ForumTopic.type.in_(self.types))

		if self.limit:
			query = query.limit(self.limit)

		return query
