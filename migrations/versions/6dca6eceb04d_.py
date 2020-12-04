"""empty message

Revision ID: 6dca6eceb04d
Revises: fd25bf3e57c3
Create Date: 2020-01-18 17:32:21.885068

"""
from alembic import op
from sqlalchemy_searchable import sync_trigger


# revision identifiers, used by Alembic.
revision = '6dca6eceb04d'
down_revision = 'fd25bf3e57c3'
branch_labels = None
depends_on = None


def upgrade():
	conn = op.get_bind()
	sync_trigger(conn, 'package', 'search_vector', ["name", "title", "short_desc", "desc"])
	op.create_check_constraint("name_valid", "package", "name ~* '^[a-z0-9_]+$'")


def downgrade():
	conn = op.get_bind()
	sync_trigger(conn, 'package', 'search_vector', ["title", "short_desc", "desc"])
	op.drop_constraint("name_valid", "package", type_="check")
