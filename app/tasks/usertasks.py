# ContentDB
# Copyright (C) 2021 rubenwardy
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

from sqlalchemy import or_, and_

from app.models import User, db, UserRank, ThreadReply, Package
from app.utils.models import create_session
from app.tasks import celery


@celery.task()
def delete_inactive_users():
	threshold = datetime.datetime.now() - datetime.timedelta(hours=5)

	users = User.query.filter(User.is_active == False, User.packages == None, User.forum_topics == None,
			User.created_at <= threshold, User.rank == UserRank.NOT_JOINED).all()
	for user in users:
		db.session.delete(user)

	db.session.commit()


@celery.task()
def upgrade_new_members():
	with create_session() as session:
		threshold = datetime.datetime.now() - datetime.timedelta(days=7)

		session.query(User).filter(and_(User.rank == UserRank.NEW_MEMBER, or_(
				User.replies.any(ThreadReply.created_at < threshold),
				User.packages.any(Package.approved_at < threshold)))).update({"rank": UserRank.MEMBER}, synchronize_session=False)

		session.commit()
