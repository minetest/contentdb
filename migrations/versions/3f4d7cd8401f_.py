"""empty message

Revision ID: 3f4d7cd8401f
Revises: 13113e5710da
Create Date: 2018-05-25 17:53:13.215127

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '3f4d7cd8401f'
down_revision = '13113e5710da'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    conn.execute(text("ALTER TYPE packagepropertykey ADD VALUE 'harddeps'"))
    conn.execute(text("ALTER TYPE packagepropertykey ADD VALUE 'softdeps'"))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
