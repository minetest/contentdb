"""empty message

Revision ID: d4262fb15b37
Revises: 8ee3cf3fb312
Create Date: 2021-07-22 10:59:03.217264

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd4262fb15b37'
down_revision = '8ee3cf3fb312'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tag', sa.Column('is_protected', sa.Boolean(), nullable=False, server_default="false"))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tag', 'is_protected')
    # ### end Alembic commands ###
