"""empty message

Revision ID: b254f55eadd2
Revises: 4e482c47e519
Create Date: 2018-05-27 23:51:11.008936

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'b254f55eadd2'
down_revision = '4e482c47e519'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    conn.execute(text("ALTER TYPE userrank ADD VALUE 'TRUSTED_MEMBER'"))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
