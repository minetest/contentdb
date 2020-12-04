"""empty message

Revision ID: df66c78e6791
Revises: a0f6c8743362
Create Date: 2020-01-24 18:39:58.363417

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'df66c78e6791'
down_revision = 'a0f6c8743362'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('api_token', sa.Column('package_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'api_token', 'package', ['package_id'], ['id'])


def downgrade():
    op.drop_constraint(None, 'api_token', type_='foreignkey')
    op.drop_column('api_token', 'package_id')
