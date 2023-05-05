# ContentDB
# Copyright (C) 2021-23 rubenwardy
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


import datetime, requests
import os
import sys

from sqlalchemy import or_, and_

from app import app
from app.models import User, db, UserRank, ThreadReply, Package
from app.utils import randomString
from app.utils.models import create_session
from app.tasks import celery, TaskError


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


@celery.task()
def set_profile_picture_from_url(username: str, url: str):
	print("### Setting pp for " + username + " to " + url, file=sys.stderr)
	user = User.query.filter_by(username=username).first()
	if user is None:
		raise TaskError(f"Unable to find user {username}")

	headers = {"Accept": "image/jpeg, image/png, image/gif"}
	resp = requests.get(url, stream=True, headers=headers, timeout=15)
	if resp.status_code != 200:
		raise TaskError(f"Failed to download {url}: {resp.status_code}: {resp.reason}")

	content_type = resp.headers["content-type"]
	if content_type is None:
		raise TaskError("Content-Type needed")
	elif content_type == "image/jpeg":
		ext = "jpg"
	elif content_type == "image/png":
		ext = "png"
	elif content_type == "image/gif":
		ext = "gif"
	else:
		raise TaskError(f"Unacceptable content-type: {content_type}")

	filename = randomString(10) + "." + ext
	filepath = os.path.join(app.config["UPLOAD_DIR"], filename)
	with open(filepath, "wb") as f:
		size = 0
		for chunk in resp.iter_content(chunk_size=1024):
			if chunk:  # filter out keep-alive new chunks
				size += len(chunk)
				if size > 3 * 1000 * 1000:  # 3 MB
					raise TaskError(f"File too large to download {url}")

				f.write(chunk)

	user.profile_pic = "/uploads/" + filename
	db.session.commit()

	return filepath
