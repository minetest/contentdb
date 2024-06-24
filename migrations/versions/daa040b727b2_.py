"""empty message

Revision ID: daa040b727b2
Revises: 097ce5d114d9
Create Date: 2024-06-22 13:57:51.857616

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "daa040b727b2"
down_revision = "097ce5d114d9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("package_release", schema=None) as batch_op:
        batch_op.add_column(sa.Column("name", sa.String(length=30), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("release_notes", sa.UnicodeText(), nullable=True))
        batch_op.alter_column("releaseDate", nullable=False, new_column_name="created_at")
        batch_op.execute("""
            UPDATE package_release SET name = title WHERE length(title) <= 30;
            UPDATE package_release SET name = TO_CHAR(created_at, 'YYYY-MM-DD') WHERE name = '';
        """)



def downgrade():
    with op.batch_alter_table("package_release", schema=None) as batch_op:
        batch_op.alter_column("created_at", nullable=False, new_column_name="releaseDate")
        batch_op.drop_column("release_notes")
        batch_op.drop_column("name")
