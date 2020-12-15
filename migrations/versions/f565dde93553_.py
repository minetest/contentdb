"""empty message

Revision ID: f565dde93553
Revises: 4585ce5147b8
Create Date: 2020-12-15 21:49:19.190893

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f565dde93553'
down_revision = '4585ce5147b8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('package_update_config', sa.Column('ref', sa.String(length=41), nullable=True))
    op.add_column('user_notification_preferences', sa.Column('pref_bot', sa.Integer(), nullable=True, server_default=None))
    op.execute("""UPDATE user_notification_preferences SET pref_bot=pref_new_thread""")
    op.alter_column('user_notification_preferences', 'pref_bot',
            existing_type=sa.INTEGER(),
            nullable=False)

    op.execute("COMMIT")
    op.execute("ALTER TYPE notificationtype ADD VALUE 'BOT'")


def downgrade():
    op.drop_column('user_notification_preferences', 'pref_bot')
    op.drop_column('package_update_config', 'ref')
