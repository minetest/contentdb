"""empty message

Revision ID: 96a01fe23389
Revises: cd5ab8a01f4a
Create Date: 2021-11-24 17:12:33.893988

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '96a01fe23389'
down_revision = 'cd5ab8a01f4a'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(text("DELETE FROM user_email_verification"))
    op.add_column('user', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('user_email_verification', sa.Column('created_at', sa.DateTime(), nullable=False))


def downgrade():

    op.drop_column('user_email_verification', 'created_at')
    op.drop_column('user', 'created_at')
