"""empty message

Revision ID: c5e4213721dd
Revises: 9832944cd1e4
Create Date: 2020-07-15 17:54:33.738132

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5e4213721dd'
down_revision = '9832944cd1e4'
branch_labels = None
depends_on = None


def upgrade():
	op.add_column('tag', sa.Column('views', sa.Integer(), nullable=False, server_default="0"))


def downgrade():
	op.drop_column('tag', 'views')
