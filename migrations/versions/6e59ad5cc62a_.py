"""empty message

Revision ID: 6e59ad5cc62a
Revises: 8425c06b7d77
Create Date: 2022-06-25 02:39:15.959553

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6e59ad5cc62a'
down_revision = '8425c06b7d77'
branch_labels = None
depends_on = None


def upgrade():
	op.drop_constraint("name_valid", "package", type_="check")
	op.create_check_constraint("name_valid", "package", "name ~* '^[a-z0-9_]+$' AND name != '_game'")


def downgrade():
	op.drop_constraint("name_valid", "package", type_="check")
	op.create_check_constraint("name_valid", "package", "name ~* '^[a-z0-9_]+$'")
