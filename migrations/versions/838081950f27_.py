"""empty message

Revision ID: 838081950f27
Revises: 86512692b770
Create Date: 2020-07-12 01:33:19.499459

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '838081950f27'
down_revision = '86512692b770'
branch_labels = None
depends_on = None


def upgrade():
	op.create_check_constraint("mp_name_valid", "meta_package", "name ~* '^[a-z0-9_]+$'")

	op.execute("""
		DELETE FROM provides AS t USING meta_package AS m WHERE t.metapackage_id = m.id AND NOT (m.name ~* '^[a-z0-9_]+$');
		DELETE FROM dependency AS t USING meta_package AS m WHERE t.meta_package_id = m.id AND NOT (m.name ~* '^[a-z0-9_]+$');
		DELETE FROM meta_package WHERE NOT (name ~* '^[a-z0-9_]+$');
	""")


def downgrade():
	op.drop_constraint("mp_name_valid", "meta_package", type_="check")
