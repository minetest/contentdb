"""empty message

Revision ID: 1fe2e44cf565
Revises: d73078c5d619
Create Date: 2024-03-30 16:19:47.384716

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1fe2e44cf565'
down_revision = 'd73078c5d619'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('github_user_id', sa.Integer(), nullable=True))
        batch_op.create_unique_constraint("_user_github_user_id", ['github_user_id'])


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint("_user_github_user_id", type_='unique')
        batch_op.drop_column('github_user_id')
