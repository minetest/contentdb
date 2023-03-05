"""empty message

Revision ID: aa53b4d36c50
Revises: ea83ce985e55
Create Date: 2023-03-05 18:11:29.743388

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'aa53b4d36c50'
down_revision = 'ea83ce985e55'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('package', sa.Column('donate_url', sa.String(length=200), nullable=True))


def downgrade():
    op.drop_column('package', 'donate_url')
