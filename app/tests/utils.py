import pytest
from app import app
from app.models import db, User
from app.default_data import populate

def clear_data(session):
	meta = db.metadata
	for table in reversed(meta.sorted_tables):
		session.execute(f'ALTER TABLE "{table.name}" DISABLE TRIGGER ALL;')
		session.execute(table.delete())
		session.execute(f'ALTER TABLE "{table.name}" ENABLE TRIGGER ALL;')
		#session.execute(table.delete())

def recreate_db():
	clear_data(db.session)
	populate(db.session)
	db.session.commit()


@pytest.fixture
def client():
	app.config["TESTING"] = True

	recreate_db()
	assert User.query.count() == 1

	with app.test_client() as client:
		yield client

	app.config["TESTING"] = False
