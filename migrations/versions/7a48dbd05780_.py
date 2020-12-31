"""empty message

Revision ID: 7a48dbd05780
Revises: df66c78e6791
Create Date: 2020-01-24 21:52:49.744404

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '7a48dbd05780'
down_revision = 'df66c78e6791'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('github_access_token', sa.String(length=50), nullable=True, server_default=None))


def downgrade():
    op.drop_column('user', 'github_access_token')
