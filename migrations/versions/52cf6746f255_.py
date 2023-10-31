"""empty message

Revision ID: 52cf6746f255
Revises: 9395ba96f853
Create Date: 2023-10-31 19:56:58.249938

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '52cf6746f255'
down_revision = '9395ba96f853'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('oauth_client', schema=None) as batch_op:
        batch_op.add_column(sa.Column('description', sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column('approved', sa.Boolean(), nullable=False, server_default="false"))
        batch_op.add_column(sa.Column('verified', sa.Boolean(), nullable=False, server_default="false"))
        batch_op.alter_column('title',
               existing_type=sa.VARCHAR(length=64),
               nullable=False)
        batch_op.alter_column('secret',
               existing_type=sa.VARCHAR(length=32),
               nullable=False)
        batch_op.alter_column('redirect_url',
               existing_type=sa.VARCHAR(length=128),
               nullable=False)


def downgrade():
    with op.batch_alter_table('oauth_client', schema=None) as batch_op:
        batch_op.drop_column('verified')
        batch_op.drop_column('approved')
        batch_op.drop_column('description')
