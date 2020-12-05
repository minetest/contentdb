"""empty message

Revision ID: 81de25b72f66
Revises: c154912eaa0c
Create Date: 2020-12-05 03:38:42.004388

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy.dialects import postgresql

revision = '81de25b72f66'
down_revision = 'c154912eaa0c'
branch_labels = None
depends_on = None


def upgrade():
    status = postgresql.ENUM('OTHER', 'PACKAGE_EDIT', 'PACKAGE_APPROVAL', 'NEW_THREAD', 'NEW_REVIEW', 'THREAD_REPLY', 'MAINTAINER', 'EDITOR_ALERT', 'EDITOR_MISC', name='notificationtype')
    status.create(op.get_bind())

    op.add_column('notification', sa.Column('emailed', sa.Boolean(), nullable=False, server_default="true"))
    op.add_column('notification', sa.Column('type', sa.Enum('OTHER', 'PACKAGE_EDIT', 'PACKAGE_APPROVAL', 'NEW_THREAD', 'NEW_REVIEW', 'THREAD_REPLY', 'MAINTAINER', 'EDITOR_ALERT', 'EDITOR_MISC', name='notificationtype'), nullable=False, server_default="OTHER"))


def downgrade():
    op.drop_column('notification', 'type')
    op.drop_column('notification', 'emailed')
