"""empty message

Revision ID: f0622f7671d5
Revises: 49105d276908
Create Date: 2023-10-31 16:04:57.708933

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f0622f7671d5'
down_revision = '49105d276908'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('oauth_client',
    sa.Column('id', sa.String(length=24), nullable=False),
    sa.Column('title', sa.String(length=64), nullable=True),
    sa.Column('secret', sa.String(length=32), nullable=True),
    sa.Column('redirect_url', sa.String(length=128), nullable=True),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('title')
    )
    with op.batch_alter_table('api_token', schema=None) as batch_op:
        batch_op.add_column(sa.Column('client_id', sa.String(length=24), nullable=True))
        batch_op.create_foreign_key(None, 'oauth_client', ['client_id'], ['id'])


def downgrade():
    with op.batch_alter_table('api_token', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('client_id')

    op.drop_table('oauth_client')
