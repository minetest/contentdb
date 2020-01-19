import pytest
from app import app
from app.default_data import populate_test_data
from app.models import db, License, Tag, User, UserRank
from utils import client, recreate_db

def test_homepage_empty(client):
	"""Start with a blank database."""

	rv = client.get("/")
	assert b"No packages available" in rv.data and b"packagetile" not in rv.data


def test_homepage_with_contents(client):
	"""Start with a test database."""

	licenses = { x.name : x for x in License.query.all() }
	tags = { x.name : x for x in Tag.query.all() }
	admin_user = User.query.filter_by(rank=UserRank.ADMIN).first()

	populate_test_data(db.session, licenses, tags, admin_user)
	db.session.commit()

	rv = client.get("/")

	assert b"No packages available" not in rv.data and b"packagetile" in rv.data
