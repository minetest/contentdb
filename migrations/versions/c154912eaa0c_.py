"""empty message

Revision ID: c154912eaa0c
Revises: 7f166b5218d7
Create Date: 2020-12-05 02:29:16.706564

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c154912eaa0c'
down_revision = '7f166b5218d7'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("COMMIT")
    op.execute("ALTER TYPE auditseverity ADD VALUE 'USER'")

def downgrade():
    pass
