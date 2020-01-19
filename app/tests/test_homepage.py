import pytest
from app import app
from utils import client, recreate_db

def test_homepage_ok(client):
	"""Start with a blank database."""

	assert app.config["TESTING"]

	rv = client.get("/")
	assert b"No packages available" in rv.data
