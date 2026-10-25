"""add order status history

Revision ID: a9b8c7d6e5f4
Revises: f1a2b3c4d5e6
Create Date: 2026-10-25

"""
from alembic import op
import sqlalchemy as sa


revision = 'a9b8c7d6e5f4'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'order_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('from_status', sa.String(length=25), nullable=True),
        sa.Column('to_status', sa.String(length=25), nullable=False),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('tracking_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name='fk_order_status_history_order_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], name='fk_order_status_history_changed_by', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('order_status_history', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_order_status_history_order_id'), ['order_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_order_status_history_changed_by'), ['changed_by'], unique=False)

    op.execute(
        "INSERT INTO order_status_history (order_id, from_status, to_status, changed_by, created_at) "
        "SELECT id, NULL, 'waiting_for_payment', user_id, COALESCE(ordered_at, CURRENT_TIMESTAMP) FROM orders"
    )


def downgrade():
    with op.batch_alter_table('order_status_history', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_order_status_history_changed_by'))
        batch_op.drop_index(batch_op.f('ix_order_status_history_order_id'))
    op.drop_table('order_status_history')
