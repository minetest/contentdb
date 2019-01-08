from .models import db, PackageType, Package, ForumTopic, License
from .utils import isNo
from sqlalchemy.sql.expression import func
from flask import abort

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

		self.title  = title
		self.types  = types
		self.search = args.get("q")
		self.random = "random" in args
		self.lucky  = self.random or "lucky" in args
		self.hide_nonfree = isNo(args.get("nonfree"))
		self.limit  = 1 if self.lucky else None
		self.order_by  = args.get("sort") or "score"
		self.order_dir = args.get("order") or "desc"

	def buildPackageQuery(self):
		query = Package.query.filter_by(soft_deleted=False, approved=True)

		if len(self.types) > 0:
			query = query.filter(Package.type.in_(self.types))

		if self.search is not None and self.search.strip() != "":
			query = query.filter(Package.title.ilike('%' + self.search + '%'))

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

		if self.limit:
			query = query.limit(self.limit)

		return query

	def buildTopicQuery(self):
		topics = ForumTopic.query \
				.filter(~ db.exists().where(Package.forums==ForumTopic.topic_id)) \
				.order_by(db.asc(ForumTopic.wip), db.asc(ForumTopic.name), db.asc(ForumTopic.title)) \
				.filter(ForumTopic.title.ilike('%' + self.search + '%'))

		if len(self.types) > 0:
			topics = topics.filter(ForumTopic.type.in_(self.types))

		if self.hide_nonfree:
			topics = topics \
                .filter(Package.license.has(License.is_foss == True)) \
                .filter(Package.media_license.has(License.is_foss == True))

		if self.limit:
			topics = topics.limit(self.limit)

		return topics
