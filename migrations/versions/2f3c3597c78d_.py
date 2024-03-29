"""empty message

Revision ID: 2f3c3597c78d
Revises: 9ec17b558413
Create Date: 2019-01-29 02:43:08.865695

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_searchable import sync_trigger
from sqlalchemy_utils.types import TSVectorType

# revision identifiers, used by Alembic.
revision = '2f3c3597c78d'
down_revision = '9ec17b558413'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('package', 'shortDesc', nullable=False, new_column_name='short_desc')
    op.add_column('package', sa.Column('search_vector', TSVectorType("title", "short_desc", "desc"), nullable=True))
    op.create_index('ix_package_search_vector', 'package', ['search_vector'], unique=False, postgresql_using='gin')

    conn = op.get_bind()
    # sync_trigger(conn, 'package', 'search_vector', ["title", "short_desc", "desc"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_package_search_vector', table_name='package')
    op.drop_column('package', 'search_vector')
    # ### end Alembic commands ###
