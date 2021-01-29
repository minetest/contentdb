"""empty message

Revision ID: 96811eb565c1
Revises: a337bcc165c0
Create Date: 2021-01-29 23:14:37.806520

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '96811eb565c1'
down_revision = 'a337bcc165c0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('package_update_config', sa.Column('auto_created', sa.Boolean(), nullable=False, server_default="false"))


def downgrade():
    op.drop_column('package_update_config', 'auto_created')
