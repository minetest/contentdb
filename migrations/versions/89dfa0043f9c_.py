"""empty message

Revision ID: 89dfa0043f9c
Revises: 2ecff2f9972d
Create Date: 2023-08-14 15:26:43.670064

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '89dfa0043f9c'
down_revision = '2ecff2f9972d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('collection',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Unicode(length=100), nullable=False),
    sa.Column('title', sa.Unicode(length=100), nullable=False),
    sa.Column('short_description', sa.Unicode(length=200), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('private', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('author_id', 'name', name='_collection_uc')
    )

    op.create_table('collection_package',
    sa.Column('package_id', sa.Integer(), nullable=False),
    sa.Column('collection_id', sa.Integer(), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['collection_id'], ['collection.id'], ),
    sa.ForeignKeyConstraint(['package_id'], ['package.id'], ),
    sa.PrimaryKeyConstraint('package_id', 'collection_id')
    )

    op.create_check_constraint("collection_name_valid", "collection",
        "name ~* '^[a-z0-9_]+$' AND name != '_game'")
    op.create_check_constraint("collection_description_nonempty", "collection_package",
        "description = NULL OR description != ''")

def downgrade():
    op.drop_constraint("collection_name_valid", "collection", type_="check")
    op.drop_constraint("collection_description_nonempty", "collection_package", type_="check")
    op.drop_table('collection_package')
    op.drop_table('collection')
    # ### end Alembic commands ###
