"""empty message

Revision ID: 49105d276908
Revises: 7a749a6c8c3a
Create Date: 2023-10-01 23:25:24.870407

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '49105d276908'
down_revision = '7a749a6c8c3a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('package', schema=None) as batch_op:
        batch_op.create_unique_constraint('_package_uc', ['author_id', 'name'])


def downgrade():
    with op.batch_alter_table('package', schema=None) as batch_op:
        batch_op.drop_constraint('_package_uc', type_='unique')
