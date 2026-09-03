"""update orders status check constraint

Revision ID: 21f6d8e04138
Revises: d0e1f2a3b4c5
Create Date: 2026-09-03 05:26:45.847811

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '21f6d8e04138'
down_revision = 'd0e1f2a3b4c5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_constraint('ck_orders_status_valid', type_='check')
        batch_op.create_check_constraint(
            'ck_orders_status_valid',
            "status IN ('waiting_for_payment', 'paid', 'processing', 'shipped', 'delivered', 'returned', 'cancelled')"
        )


def downgrade():
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_constraint('ck_orders_status_valid', type_='check')
        batch_op.create_check_constraint(
            'ck_orders_status_valid',
            "status IN ('waiting_for_payment', 'processing', 'shipped', 'delivered', 'cancelled')"
        )
