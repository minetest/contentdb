"""empty message

Revision ID: 43dc7dbf64c8
Revises: c1ea65e2b492
Create Date: 2020-12-09 19:06:11.891807

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43dc7dbf64c8'
down_revision = 'c1ea65e2b492'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('audit_log_entry', 'causer_id',
            existing_type=sa.INTEGER(),
            nullable=True)


def downgrade():
    op.alter_column('audit_log_entry', 'causer_id',
            existing_type=sa.INTEGER(),
            nullable=False)
