from app.default_data import populate_test_data
from app.models import db
from .utils import client # noqa


def test_homepage_empty(client):
	"""Start with a blank database."""

	rv = client.get("/")
	assert b"No packages available" in rv.data and b"packagetile" not in rv.data


def test_homepage_with_contents(client):
	"""Start with a test database."""

	populate_test_data(db.session)
	db.session.commit()

	rv = client.get("/")

	assert b"No packages available" not in rv.data and b"packagetile" in rv.data
