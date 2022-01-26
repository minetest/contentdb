"""empty message

Revision ID: f6ef5f35abca
Revises: 011e42c52d21
Create Date: 2022-01-26 00:10:46.610784

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f6ef5f35abca'
down_revision = '011e42c52d21'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('package_screenshot', sa.Column('height', sa.Integer(), nullable=False, server_default="0"))
    op.add_column('package_screenshot', sa.Column('width', sa.Integer(), nullable=False, server_default="0"))


def downgrade():
    op.drop_column('package_screenshot', 'width')
    op.drop_column('package_screenshot', 'height')
