"""empty message

Revision ID: 9395ba96f853
Revises: dd17239f7144
Create Date: 2023-10-31 17:39:27.957209

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9395ba96f853'
down_revision = 'dd17239f7144'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('oauth_client', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=False))

def downgrade():
    with op.batch_alter_table('oauth_client', schema=None) as batch_op:
        batch_op.drop_column('created_at')
