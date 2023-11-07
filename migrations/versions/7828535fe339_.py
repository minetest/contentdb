"""empty message

Revision ID: 7828535fe339
Revises: 52cf6746f255
Create Date: 2023-11-07 22:51:39.450652

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7828535fe339'
down_revision = '52cf6746f255'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('collection', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pinned', sa.Boolean(), nullable=False, server_default="false"))

    with op.batch_alter_table('oauth_client', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_clientside', sa.Boolean(), nullable=False, server_default="false"))


def downgrade():
    with op.batch_alter_table('oauth_client', schema=None) as batch_op:
        batch_op.drop_column('is_clientside')

    with op.batch_alter_table('collection', schema=None) as batch_op:
        batch_op.drop_column('pinned')
