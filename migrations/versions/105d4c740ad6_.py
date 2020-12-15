"""empty message

Revision ID: 105d4c740ad6
Revises: 886c92dc6eaa
Create Date: 2020-12-15 17:28:56.559801

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import orm
from app.models import User, UserRank

revision = '105d4c740ad6'
down_revision = '886c92dc6eaa'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("COMMIT")
    op.execute("ALTER TYPE userrank ADD VALUE 'BOT' AFTER 'EDITOR'")

    conn = op.get_bind()
    system_user = User("ContentDB", active=False)
    system_user.rank = UserRank.BOT

    session = orm.Session(bind=conn)
    session.add(system_user)
    session.commit()


def downgrade():
    pass
