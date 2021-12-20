"""empty message

Revision ID: 17b303f33f68
Revises: 96a01fe23389
Create Date: 2021-12-20 19:48:58.571336

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '17b303f33f68'
down_revision = '96a01fe23389'
branch_labels = None
depends_on = None


def upgrade():
    status = postgresql.ENUM('WIP', 'BETA', 'ACTIVELY_DEVELOPED', 'MAINTENANCE_ONLY', 'AS_IS', 'DEPRECATED', 'LOOKING_FOR_MAINTAINER', name='packagedevstate')
    status.create(op.get_bind())

    op.add_column('package', sa.Column('dev_state', sa.Enum('WIP', 'BETA', 'ACTIVELY_DEVELOPED', 'MAINTENANCE_ONLY', 'AS_IS', 'DEPRECATED', 'LOOKING_FOR_MAINTAINER', name='packagedevstate'), nullable=True))


def downgrade():
    op.drop_column('package', 'dev_state')
