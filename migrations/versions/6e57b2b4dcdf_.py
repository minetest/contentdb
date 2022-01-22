"""empty message

Revision ID: 6e57b2b4dcdf
Revises: 17b303f33f68
Create Date: 2022-01-22 20:35:25.494712
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6e57b2b4dcdf'
down_revision = '17b303f33f68'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('locale', sa.String(length=10), nullable=True))


def downgrade():
    op.drop_column('user', 'locale')
