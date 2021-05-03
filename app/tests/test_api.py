from app.default_data import populate_test_data
from app.models import db, Package, PackageState
from utils import parse_json, is_str, is_int, is_optional
from .utils import client # noqa


def validate_package_list(packages, strict=False):
	valid_keys = {
		"author", "name", "release",
		"short_description", "thumbnail",
		"title", "type"
	}

	for package in packages:
		assert set(package.keys()).issubset(valid_keys)

		assert is_str(package.get("author"))
		assert is_str(package.get("name"))
		if strict:
			assert is_int(package.get("release"))
		else:
			assert is_optional(int, package.get("release"))
		assert is_str(package.get("short_description"))
		assert is_optional(str, package.get("thumbnail"))
		assert is_str(package.get("title"))
		assert is_str(package.get("type"))


def test_packages_empty(client):
	"""Start with a blank database."""

	rv = client.get("/api/packages/")
	assert parse_json(rv.data) == []


def test_packages_with_contents(client):
	"""Start with a test database."""


	populate_test_data(db.session)
	db.session.commit()

	rv = client.get("/api/packages/")

	packages = parse_json(rv.data)

	assert len(packages) > 0
	assert len(packages) == Package.query.filter_by(state=PackageState.APPROVED).count()

	validate_package_list(packages)


def test_packages_with_query(client):
	"""Start with a test database."""

	populate_test_data(db.session)
	db.session.commit()

	rv = client.get("/api/packages/?q=food")

	packages = parse_json(rv.data)

	assert len(packages) == 2

	validate_package_list(packages)

	assert (packages[0]["name"] == "food" and packages[1]["name"] == "food_sweet") or \
		(packages[1]["name"] == "food" and packages[0]["name"] == "food_sweet")


def test_packages_with_protocol_high(client):
	"""Start with a test database."""

	populate_test_data(db.session)
	db.session.commit()

	rv = client.get("/api/packages/?protocol_version=40")

	packages = parse_json(rv.data)

	assert len(packages) == 4

	for package in packages:
		assert package["name"] != "mesecons"

	validate_package_list(packages, True)


def test_packages_with_protocol_low(client):
	"""Start with a test database."""

	populate_test_data(db.session)
	db.session.commit()

	rv = client.get("/api/packages/?protocol_version=20")

	packages = parse_json(rv.data)

	assert len(packages) == 4

	for package in packages:
		assert package["name"] != "awards"

	validate_package_list(packages, True)
