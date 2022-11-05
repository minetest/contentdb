"""empty message

Revision ID: ea83ce985e55
Revises: 16eb610b7751
Create Date: 2022-11-05 22:09:50.875158

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ea83ce985e55'
down_revision = '16eb610b7751'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('package_daily_stats',
    sa.Column('package_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('platform_minetest', sa.Integer(), nullable=False),
    sa.Column('platform_other', sa.Integer(), nullable=False),
    sa.Column('reason_new', sa.Integer(), nullable=False),
    sa.Column('reason_dependency', sa.Integer(), nullable=False),
    sa.Column('reason_update', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['package_id'], ['package.id'], ),
    sa.PrimaryKeyConstraint('package_id', 'date')
    )


def downgrade():
    op.drop_table('package_daily_stats')
