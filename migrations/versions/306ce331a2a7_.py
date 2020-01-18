"""empty message

Revision ID: 306ce331a2a7
Revises: 6dca6eceb04d
Create Date: 2020-01-18 23:00:40.487425

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '306ce331a2a7'
down_revision = '6dca6eceb04d'
branch_labels = None
depends_on = None


def upgrade():
	conn = op.get_bind()
	op.create_check_constraint("CK_approval_valid", "package_release", "not approved OR (task_id IS NULL AND NOT url = '')")


def downgrade():
	conn = op.get_bind()
	op.drop_constraint("CK_approval_valid", "package_release", type_="check")
