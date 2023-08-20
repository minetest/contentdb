"""empty message

Revision ID: 7a749a6c8c3a
Revises: 20f2aa2f40b9
Create Date: 2023-08-20 21:19:26.930069

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7a749a6c8c3a'
down_revision = '20f2aa2f40b9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tag', schema=None) as batch_op:
        batch_op.drop_column('is_protected')


def downgrade():
    with op.batch_alter_table('tag', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_protected', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False))
