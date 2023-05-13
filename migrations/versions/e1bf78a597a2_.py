"""empty message

Revision ID: e1bf78a597a2
Revises: 06d23947e7ef
Create Date: 2020-12-06 03:16:59.988464

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'e1bf78a597a2'
down_revision = '06d23947e7ef'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('package_screenshot', sa.Column('order', sa.Integer(), nullable=True))
    op.execute(text("""UPDATE package_screenshot SET "order" = id"""))
    op.alter_column('package_screenshot', 'order', nullable=False)


def downgrade():
    op.drop_column('package_screenshot', 'order')
