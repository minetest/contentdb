"""empty message

Revision ID: dd17239f7144
Revises: f0622f7671d5
Create Date: 2023-10-31 16:29:08.892647

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dd17239f7144'
down_revision = 'f0622f7671d5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('api_token', schema=None) as batch_op:
        batch_op.add_column(sa.Column('auth_code', sa.String(length=34), nullable=True))
        batch_op.create_unique_constraint(None, ['auth_code'])


def downgrade():
    with op.batch_alter_table('api_token', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('auth_code')
