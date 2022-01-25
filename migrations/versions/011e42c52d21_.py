"""empty message

Revision ID: 011e42c52d21
Revises: 6e57b2b4dcdf
Create Date: 2022-01-25 18:48:46.367409

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011e42c52d21'
down_revision = '6e57b2b4dcdf'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('package', sa.Column('video_url', sa.String(length=200), nullable=True))



def downgrade():
    op.drop_column('package', 'video_url')