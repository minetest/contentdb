"""empty message

Revision ID: 8ee3cf3fb312
Revises: e82c2141fae3
Create Date: 2021-05-03 22:21:02.167758

"""
from alembic import op
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8ee3cf3fb312'
down_revision = 'e82c2141fae3'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('user', 'email_confirmed_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.execute(text("""UPDATE "user" SET email_confirmed_at = NULL WHERE email_confirmed_at < '2016-01-01'::date"""))


def downgrade():
    op.alter_column('user', 'email_confirmed_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.execute(
            text("""UPDATE "user" SET email_confirmed_at = '2004-01-01'::date WHERE email_confirmed_at IS NULL"""))
