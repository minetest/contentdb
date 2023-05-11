"""empty message

Revision ID: 23afcf580aae
Revises: dabd7ab14339
Create Date: 2023-05-11 22:02:24.021652

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '23afcf580aae'
down_revision = 'dabd7ab14339'
branch_labels = None
depends_on = None


def upgrade():
    op.create_check_constraint("ck_license_txp", "package", "type != 'TXP' OR license_id = media_license_id")


def downgrade():
    op.drop_constraint("ck_license_txp", "package", type_="check")
