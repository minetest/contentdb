"""empty message

Revision ID: cd5ab8a01f4a
Revises: 1af840af0209
Create Date: 2021-08-18 20:47:54.268263

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cd5ab8a01f4a'
down_revision = '1af840af0209'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('package_review_vote',
    sa.Column('review_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('is_positive', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['review_id'], ['package_review.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('review_id', 'user_id')
    )
    op.add_column('package_review', sa.Column('score', sa.Integer(), nullable=False, server_default="1"))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('package_review', 'score')
    op.drop_table('package_review_vote')
    # ### end Alembic commands ###
