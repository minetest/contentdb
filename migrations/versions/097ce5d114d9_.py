"""empty message

Revision ID: 097ce5d114d9
Revises: 1fe2e44cf565
Create Date: 2024-06-08 09:59:23.084979

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "097ce5d114d9"
down_revision = "1fe2e44cf565"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("package_review", schema=None) as batch_op:
        batch_op.add_column(sa.Column("language_id", sa.String(), nullable=True, default=None))
        batch_op.alter_column("package_id",
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.create_foreign_key("package_review_language", "language", ["language_id"], ["id"])


def downgrade():
    with op.batch_alter_table("package_review", schema=None) as batch_op:
        batch_op.drop_constraint("package_review_language", type_="foreignkey")
        batch_op.alter_column("package_id",
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.drop_column("language_id")
