"""empty message

Revision ID: a9c1c08bf956
Revises: 43dc7dbf64c8
Create Date: 2020-12-10 16:42:28.086146

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'a9c1c08bf956'
down_revision = '43dc7dbf64c8'
branch_labels = None
def upgrade():
    op.alter_column('api_token', 'access_token', nullable=False)
    op.alter_column('package', 'author_id', nullable=False)
    op.execute(text("""UPDATE package SET "state"='WIP' WHERE "state" IS NULL"""))
    op.alter_column('package', 'state', nullable=False)
    op.alter_column('package_screenshot', 'package_id', nullable=False)
    op.alter_column('user', 'rank', nullable=False)
    op.alter_column('user_email_verification', 'user_id', nullable=False)
    op.alter_column('user_email_verification', 'email', nullable=False)
    op.alter_column('user_email_verification', 'token', nullable=False)
    op.execute(text("UPDATE notification SET created_at=NOW() WHERE created_at IS NULL"))
    op.alter_column('notification', 'created_at', nullable=False)


def downgrade():
    op.alter_column('api_token', 'access_token', nullable=True)
    op.alter_column('package', 'author_id', nullable=True)
    op.alter_column('package', 'state', nullable=True)
    op.alter_column('package_screenshot', 'package_id', nullable=True)
    op.alter_column('user', 'rank', nullable=True)
    op.alter_column('user_email_verification', 'user_id', nullable=True)
    op.alter_column('user_email_verification', 'email', nullable=True)
    op.alter_column('user_email_verification', 'token', nullable=True)
    op.alter_column('notification', 'created_at', nullable=True)



depends_on = None
