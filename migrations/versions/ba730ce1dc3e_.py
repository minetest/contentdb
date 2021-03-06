"""empty message

Revision ID: ba730ce1dc3e
Revises: 8679442b8dde
Create Date: 2020-07-11 00:59:13.519267

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba730ce1dc3e'
down_revision = '8679442b8dde'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('audit_log_entry',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('causer_id', sa.Integer(), nullable=False),
    sa.Column('severity', sa.Enum('NORMAL', 'EDITOR', 'MODERATION', name='auditseverity'), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('url', sa.String(length=200), nullable=True),
    sa.Column('package_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['causer_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['package_id'], ['package.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.alter_column('thread', 'private',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_server_default=sa.text('false'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('thread', 'private',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_server_default=sa.text('false'))
    op.drop_table('audit_log_entry')
    # ### end Alembic commands ###
