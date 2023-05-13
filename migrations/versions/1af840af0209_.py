"""empty message

Revision ID: 1af840af0209
Revises: 725ff70ea316
Create Date: 2021-08-16 17:17:12.060257

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1af840af0209'
down_revision = '725ff70ea316'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(text("COMMIT"))
    op.execute(text("ALTER TYPE userrank ADD VALUE 'APPROVER' BEFORE 'EDITOR'"))


def downgrade():
    pass
