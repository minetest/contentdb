"""empty message

Revision ID: 16eb610b7751
Revises: 76ff303f76d8
Create Date: 2022-09-14 21:10:40.126876

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
from sqlalchemy_searchable import sync_trigger

revision = '16eb610b7751'
down_revision = '76ff303f76d8'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    options = {"weights": {"name": "A", "title": "B", "short_desc": "C"}}
    # sync_trigger(conn, 'package', 'search_vector', ["name", "title", "short_desc"], options=options)


def downgrade():
    conn = op.get_bind()

    options = {"weights": {"name": "A", "title": "B", "short_desc": "C", "desc": "D"}}
    # sync_trigger(conn, 'package', 'search_vector', ["name", "title", "short_desc", "desc"], options=options)
