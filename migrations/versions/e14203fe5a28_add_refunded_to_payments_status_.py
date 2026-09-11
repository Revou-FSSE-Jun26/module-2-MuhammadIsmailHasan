"""add refunded to payments status constraint

Revision ID: e14203fe5a28
Revises: 746a951a0a3e
Create Date: 2026-09-09 03:48:29.451207

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e14203fe5a28'
down_revision = '746a951a0a3e'
branch_labels = None
depends_on = None


CONSTRAINT_NAME = 'ck_payments_status_valid'
OLD_STATUSES = "('pending', 'paid', 'expired', 'failed')"
NEW_STATUSES = "('pending', 'paid', 'expired', 'failed', 'refunded')"


def upgrade():
    # A CHECK constraint can't be altered in place; drop and recreate it.
    op.drop_constraint(CONSTRAINT_NAME, 'payments', type_='check')
    op.create_check_constraint(
        CONSTRAINT_NAME, 'payments', f"status IN {NEW_STATUSES}"
    )


def downgrade():
    op.drop_constraint(CONSTRAINT_NAME, 'payments', type_='check')
    op.create_check_constraint(
        CONSTRAINT_NAME, 'payments', f"status IN {OLD_STATUSES}"
    )
