from .models import db, PackageType, Package, ForumTopic, License, MinetestRelease, PackageRelease
from .utils import isNo
from sqlalchemy.sql.expression import func
from flask import abort
from sqlalchemy import or_

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

		hide_flags = args.getlist("hide")

		self.title  = title
		self.types  = types
		self.search = args.get("q")
		self.random = "random" in args
		self.lucky  = self.random or "lucky" in args
		self.hide_nonfree = "nonfree" in hide_flags
		self.limit  = 1 if self.lucky else None
		self.order_by  = args.get("sort") or "score"
		self.order_dir = args.get("order") or "desc"
		self.protocol_version = args.get("protocol_version")

		if self.search is not None and self.search.strip() == "":
			self.search = None

	def getMinetestVersion(self):
		if not self.protocol_version:
			return None

		self.protocol_version = int(self.protocol_version)
		version = MinetestRelease.query.filter(MinetestRelease.protocol>=self.protocol_version).first()
		if version is not None:
			return version.id
		else:
			return 10000000

	def buildPackageQuery(self):
		query = Package.query.filter_by(soft_deleted=False, approved=True)

		if len(self.types) > 0:
			query = query.filter(Package.type.in_(self.types))

		if self.search:
			query = query.search(self.search)

		if self.random:
			query = query.order_by(func.random())
		else:
			to_order = None
			if self.order_by == "score":
				to_order = Package.score
			elif self.order_by == "created_at":
				to_order = Package.created_at
			else:
				abort(400)

			if self.order_dir == "asc":
				to_order = db.asc(to_order)
			elif self.order_dir == "desc":
				to_order = db.desc(to_order)
			else:
				abort(400)

			query = query.order_by(to_order)

		if self.hide_nonfree:
			query = query.filter(Package.license.has(License.is_foss == True))
			query = query.filter(Package.media_license.has(License.is_foss == True))

		if self.protocol_version:
			version = self.getMinetestVersion()
			query = query.join(Package.releases) \
				.filter(PackageRelease.approved==True) \
				.filter(or_(PackageRelease.min_rel_id==None, PackageRelease.min_rel_id<=version)) \
				.filter(or_(PackageRelease.max_rel_id==None, PackageRelease.max_rel_id>=version))

		if self.limit:
			query = query.limit(self.limit)

		return query

	def buildTopicQuery(self):
		topics = ForumTopic.query \
				.filter(~ db.exists().where(Package.forums==ForumTopic.topic_id)) \
				.order_by(db.asc(ForumTopic.wip), db.asc(ForumTopic.name), db.asc(ForumTopic.title))

		if self.search:
			topics = topics.filter(ForumTopic.title.ilike('%' + self.search + '%'))

		if len(self.types) > 0:
			topics = topics.filter(ForumTopic.type.in_(self.types))

		if self.limit:
			topics = topics.limit(self.limit)

		return topics
