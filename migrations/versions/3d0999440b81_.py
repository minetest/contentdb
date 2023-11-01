"""empty message

Revision ID: 3d0999440b81
Revises: 52cf6746f255
Create Date: 2023-11-01 00:45:24.057951

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3d0999440b81'
down_revision = '52cf6746f255'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('api_token', schema=None) as batch_op:
        batch_op.add_column(sa.Column('scope_user_email', sa.Boolean(), nullable=False, server_default="false"))
        batch_op.add_column(sa.Column('scope_package', sa.Boolean(), nullable=False, server_default="false"))
        batch_op.add_column(sa.Column('scope_package_release', sa.Boolean(), nullable=False, server_default="false"))
        batch_op.add_column(sa.Column('scope_package_screenshot', sa.Boolean(), nullable=False, server_default="false"))

    op.execute("""
        UPDATE api_token SET
        scope_user_email = true, 
            scope_package = true,
            scope_package_release = true,
            scope_package_screenshot = true;
    """)


def downgrade():
    with op.batch_alter_table('api_token', schema=None) as batch_op:
        batch_op.drop_column('scope_package_screenshot')
        batch_op.drop_column('scope_package_release')
        batch_op.drop_column('scope_package')
        batch_op.drop_column('scope_user_email')
