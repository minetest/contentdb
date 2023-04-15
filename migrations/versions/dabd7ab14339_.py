"""empty message

Revision ID: dabd7ab14339
Revises: aa53b4d36c50
Create Date: 2023-04-15 01:18:53.212673

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dabd7ab14339'
down_revision = 'aa53b4d36c50'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('package_review', sa.Column('rating', sa.Integer(), nullable=True))
    op.execute("""
        UPDATE package_review SET rating = CASE
           WHEN recommends THEN 5
           ELSE 1
        END;
    """)
    op.drop_column('package_review', 'recommends')
    op.alter_column('package_review', 'rating', nullable=False)


def downgrade():
    op.add_column('package_review', sa.Column('recommends', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.execute("""
        UPDATE package_review SET recommends = rating >= 3;
    """)
    op.drop_column('package_review', 'rating')
    op.alter_column('package_review', 'recommends', nullable=False)
