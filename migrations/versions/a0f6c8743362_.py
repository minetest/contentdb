"""empty message

Revision ID: a0f6c8743362
Revises: 64fee8e5ab34
Create Date: 2020-01-19 19:12:39.402679

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a0f6c8743362'
down_revision = '64fee8e5ab34'
branch_labels = None
depends_on = None


def upgrade():
	op.alter_column('user', 'password',
				existing_type=sa.VARCHAR(length=255),
				nullable=False,
				existing_server_default=sa.text("''::character varying"),
				server_default='')


def downgrade():
	op.alter_column('user', 'password',
				existing_type=sa.VARCHAR(length=255),
				nullable=True,
				existing_server_default=sa.text("''::character varying"))
