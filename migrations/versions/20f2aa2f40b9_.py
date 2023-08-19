"""empty message

Revision ID: 20f2aa2f40b9
Revises: 89dfa0043f9c
Create Date: 2023-08-19 01:35:20.100549

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20f2aa2f40b9'
down_revision = '89dfa0043f9c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('collection', sa.Column('long_description', sa.UnicodeText(), nullable=True, server_default=None))


def downgrade():
    with op.batch_alter_table('collection', schema=None) as batch_op:
        batch_op.drop_column('long_description')
