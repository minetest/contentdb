"""empty message

Revision ID: 2ecff2f9972d
Revises: 23afcf580aae
Create Date: 2023-06-18 07:51:42.581955

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2ecff2f9972d'
down_revision = '23afcf580aae'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('package', schema=None) as batch_op:
        batch_op.add_column(sa.Column('supports_all_games', sa.Boolean(), nullable=False, server_default="false"))


def downgrade():
    with op.batch_alter_table('package', schema=None) as batch_op:
        batch_op.drop_column('supports_all_games')
