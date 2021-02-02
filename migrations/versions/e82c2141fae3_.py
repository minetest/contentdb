"""empty message

Revision ID: e82c2141fae3
Revises: 96811eb565c1
Create Date: 2021-02-02 17:25:04.070483

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e82c2141fae3'
down_revision = '96811eb565c1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('package_screenshot', sa.Column('created_at', sa.DateTime(), nullable=False, server_default="now()"))


def downgrade():
    op.drop_column('package_screenshot', 'created_at')
