"""empty message

Revision ID: e571b3498f9e
Revises: 3710e5fbbe87
Create Date: 2022-02-01 19:30:59.537512

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e571b3498f9e'
down_revision = '3710e5fbbe87'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('package_game_support',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('package_id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('supports', sa.Boolean(), nullable=False),
    sa.Column('confidence', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['game_id'], ['package.id'], ),
    sa.ForeignKeyConstraint(['package_id'], ['package.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('game_id', 'package_id', name='_package_game_support_uc')
    )


def downgrade():
    op.drop_table('package_game_support')
