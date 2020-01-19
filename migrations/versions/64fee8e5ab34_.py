"""empty message

Revision ID: 64fee8e5ab34
Revises: 306ce331a2a7
Create Date: 2020-01-19 02:28:05.432244

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '64fee8e5ab34'
down_revision = '306ce331a2a7'
branch_labels = None
depends_on = None


def upgrade():
	op.alter_column('user', 'confirmed_at', nullable=False, new_column_name='email_confirmed_at')


def downgrade():
	op.alter_column('user', 'email_confirmed_at', nullable=False, new_column_name='confirmed_at')
