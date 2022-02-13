"""empty message

Revision ID: 01f8d5de29e1
Revises: e571b3498f9e
Create Date: 2022-02-13 10:12:20.150232

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '01f8d5de29e1'
down_revision = 'e571b3498f9e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('user_ban',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('message', sa.UnicodeText(), nullable=False),
    sa.Column('banned_by_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['banned_by_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('user_id')
    )


def downgrade():
    op.drop_table('user_ban')
