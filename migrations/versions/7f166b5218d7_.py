"""empty message

Revision ID: 7f166b5218d7
Revises: 3f5836a3df5c
Create Date: 2020-12-05 00:06:41.466562

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f166b5218d7'
down_revision = '3f5836a3df5c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user_email_verification', sa.Column('is_password_reset', sa.Boolean(), nullable=False, server_default="false"))


def downgrade():
    op.drop_column('user_email_verification', 'is_password_reset')
