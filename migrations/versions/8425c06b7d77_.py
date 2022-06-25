"""empty message

Revision ID: 8425c06b7d77
Revises: 8807a5279793
Create Date: 2022-06-25 00:26:29.841145

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8425c06b7d77'
down_revision = '8807a5279793'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('package', sa.Column('enable_game_support_detection', sa.Boolean(), nullable=False, server_default="true"))


def downgrade():
    op.drop_column('package', 'enable_game_support_detection')
