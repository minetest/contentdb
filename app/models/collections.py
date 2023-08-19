# ContentDB
# Copyright (C) 2023  rubenwardy
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

from flask import url_for

from . import db, Permission, User, UserRank


class CollectionPackage(db.Model):
	package_id = db.Column(db.Integer, db.ForeignKey("package.id"), primary_key=True)
	package = db.relationship("Package", foreign_keys=[package_id])

	collection_id = db.Column(db.Integer, db.ForeignKey("collection.id"), primary_key=True)
	collection = db.relationship("Collection", back_populates="items", foreign_keys=[collection_id])

	order = db.Column(db.Integer, nullable=False, default=0)
	description = db.Column(db.String, nullable=True)
	created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

	collection_description_nonempty = db.CheckConstraint("description = NULL OR description != ''")


class Collection(db.Model):
	id = db.Column(db.Integer, primary_key=True)

	author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
	author = db.relationship("User", back_populates="collections", foreign_keys=[author_id])

	name = db.Column(db.Unicode(100), nullable=False)
	title = db.Column(db.Unicode(100), nullable=False)
	short_description = db.Column(db.Unicode(200), nullable=False)
	long_description = db.Column(db.UnicodeText, nullable=True)
	created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
	private = db.Column(db.Boolean, nullable=False, default=False)

	packages = db.relationship("Package", secondary=CollectionPackage.__table__, backref="collections")
	items = db.relationship("CollectionPackage", back_populates="collection", order_by=db.asc("created_at"),
		cascade="all, delete, delete-orphan")

	collection_name_valid = db.CheckConstraint("name ~* '^[a-z0-9_]+$' AND name != '_game'")
	__table_args__ = (db.UniqueConstraint("author_id", "name", name="_collection_uc"),)

	def get_url(self, endpoint, **kwargs):
		return url_for(endpoint, author=self.author.username, name=self.name, **kwargs)

	def check_perm(self, user: User, perm):
		if type(perm) == str:
			perm = Permission[perm]
		elif type(perm) != Permission:
			raise Exception("Unknown permission given to Collection.check_perm()")

		if not user.is_authenticated:
			return perm == Permission.VIEW_COLLECTION and not self.private

		can_view = not self.private or self.author == user or user.rank.at_least(UserRank.MODERATOR)
		if perm == Permission.VIEW_COLLECTION:
			return can_view
		elif perm == Permission.EDIT_COLLECTION:
			return can_view and (self.author == user or user.rank.at_least(UserRank.EDITOR))
		else:
			raise Exception("Permission {} is not related to collections".format(perm.name))
