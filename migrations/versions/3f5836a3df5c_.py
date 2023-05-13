"""empty message

Revision ID: 3f5836a3df5c
Revises: b3c7ff6655af
Create Date: 2020-12-04 22:30:33.420071

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '3f5836a3df5c'
down_revision = 'b3c7ff6655af'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('user', 'password',
               existing_type=sa.VARCHAR(length=255),
               nullable=True,
               existing_server_default=sa.text("''::character varying"))

    op.execute(text("""
        UPDATE "user" SET password=NULL WHERE password=''
    """))
    op.create_check_constraint("CK_password", "user",
            "password IS NULL OR password != ''")


def downgrade():
    op.drop_constraint("CK_password", "user", type_="check")
    op.alter_column('user', 'password',
               existing_type=sa.VARCHAR(length=255),
               nullable=False,
               existing_server_default=sa.text("''::character varying"))
