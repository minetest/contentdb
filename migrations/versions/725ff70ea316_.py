"""empty message

Revision ID: 725ff70ea316
Revises: 51be0401bb85
Create Date: 2021-07-31 19:10:36.683434

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '725ff70ea316'
down_revision = '51be0401bb85'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('license', sa.Column('url', sa.String(length=128), nullable=True, default=None))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('license', 'url')
    # ### end Alembic commands ###
