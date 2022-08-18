"""empty message

Revision ID: 76ff303f76d8
Revises: 6e59ad5cc62a
Create Date: 2022-08-18 15:41:28.411877

"""

from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy_searchable import sync_trigger

revision = '76ff303f76d8'
down_revision = '6e59ad5cc62a'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    options = {"weights": {"name": "A", "title": "B", "short_desc": "C", "desc": "D"}}
    sync_trigger(conn, 'package', 'search_vector', ["name", "title", "short_desc", "desc"], options=options)


def downgrade():
    conn = op.get_bind()
    sync_trigger(conn, 'package', 'search_vector', ["name", "title", "short_desc", "desc"])
