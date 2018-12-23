"""empty message

Revision ID: a791b9b74a4c
Revises: 44e138485931
Create Date: 2018-12-23 23:52:02.010281

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a791b9b74a4c'
down_revision = '44e138485931'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forum_topic', sa.Column('discarded', sa.Boolean(), server_default='0', nullable=True))

def downgrade():
    op.drop_column('forum_topic', 'discarded')
