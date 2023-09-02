# ContentDB
# Copyright (C) rubenwardy
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

from flask import url_for

from app.models import User, UserEmailVerification
from .utils import login, logout, is_logged_in
from .utils import client # noqa


def test_login_logout(client):
	rv = client.get("/")
	assert not is_logged_in(rv)

	assert b"Sign out" not in rv.data
	rv = login(client, "rubenwardy", "tuckfrump")
	assert b"Sign out" in rv.data
	assert is_logged_in(rv)

	rv = client.get("/")
	assert is_logged_in(rv)

	rv = logout(client)
	assert not is_logged_in(rv)

	rv = login(client, "rubenwardy", "wrongpass")
	assert b"Incorrect password. Did you set one?" in rv.data
	assert not is_logged_in(rv)

	rv = login(client, "badname", "wrongpass")
	assert b"User badname does not exist" in rv.data
	assert not is_logged_in(rv)

	rv = login(client, "bad@email.com", "wrongpass")
	assert b"Incorrect email or password" in rv.data
	assert not is_logged_in(rv)


def register(client, username, display_name, password, email, question):
	return client.post("/user/register/", data=dict(
			username=username,
			display_name=display_name,
			email=email,
			password=password,
			question=question,
			agree=True
	), follow_redirects=True)


def test_register(client):
	username = "testuser123"
	password = "VYjNnjdDPhCVUZx"
	assert User.query.filter_by(username=username).first() is None

	rv = register(client, username, "Test User", "password", "test@example.com", "13")
	assert b"Field must be between 12 and 100 characters long." in rv.data

	rv = register(client, username, "Test User", password, "test@example.com", "13")
	assert b"Incorrect captcha answer" in rv.data

	rv = register(client, "££££!!!", "Test User", password, "test@example.com", "13")
	assert b"invalid-feedback" in rv.data
	assert b"Only alphabetic letters (A-Za-z), numbers (0-9), underscores (_), minuses (-), and periods (.) allowed</p>" in rv.data


def test_register_flow(client):
	username = "testuser123"
	password = "VYjNnjdDPhCVUZx"

	assert User.query.filter_by(username=username).first() is None

	rv = register(client, username, "Test User", password, "test@example.com", "19")
	assert b"We've sent an email to the address you specified" in rv.data

	user = User.query.filter_by(username=username).first()
	assert user is not None
	assert user.username == username
	assert user.display_name == "Test User"
	assert not user.is_active
	assert user.email_confirmed_at is None
	assert user.email == "test@example.com"

	rv = login(client, username, password)
	assert b"You need to confirm the registration email" in rv.data
	assert not is_logged_in(rv)

	email = UserEmailVerification.query.filter_by(user_id=user.id).first()
	assert email is not None

	rv = client.get(url_for('users.verify_email', token=email.token), follow_redirects=True)
	assert b"You may now log in" in rv.data

	assert b"Sign out" not in rv.data
	rv = login(client, username, password)
	assert b"Sign out" in rv.data
	assert is_logged_in(rv)
