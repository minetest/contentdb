"""empty message

Revision ID: 8807a5279793
Revises: 01f8d5de29e1
Create Date: 2022-04-23 19:45:00.301875

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '8807a5279793'
down_revision = '01f8d5de29e1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('thread_reply', sa.Column('is_status_update', sa.Boolean(), server_default='0', nullable=False))


def downgrade():
    op.drop_column('thread_reply', 'is_status_update')
