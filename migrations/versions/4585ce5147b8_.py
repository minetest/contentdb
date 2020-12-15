"""empty message

Revision ID: 4585ce5147b8
Revises: 105d4c740ad6
Create Date: 2020-12-15 21:35:18.982716

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4585ce5147b8'
down_revision = '105d4c740ad6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('package_update_config', sa.Column('outdated', sa.Boolean(), nullable=False, server_default="false"))


def downgrade():
    op.drop_column('package_update_config', 'outdated')
