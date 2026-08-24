"""rebuild order_items as full model with unit_price, quantity, sub_total

Revision ID: a1b2c3d4e5f6
Revises: 9a308900b370
Create Date: 2026-08-24

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = '9a308900b370'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('order_items')

    op.create_table('order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=11, scale=2), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('sub_total', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name='fk_order_items_order_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_order_items_product_id', ondelete='RESTRICT'),
        sa.CheckConstraint('quantity > 0', name='ck_order_items_quantity_positive'),
        sa.CheckConstraint('unit_price >= 0', name='ck_order_items_unit_price_non_negative'),
        sa.CheckConstraint('sub_total >= 0', name='ck_order_items_sub_total_non_negative'),
        sa.PrimaryKeyConstraint('id')
    )

    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.create_index('ix_order_items_order_id', ['order_id'], unique=False)
        batch_op.create_index('ix_order_items_product_id', ['product_id'], unique=False)

    op.drop_constraint('ck_orders_status_valid', 'orders', type_='check')
    op.create_check_constraint(
        'ck_orders_status_valid',
        'orders',
        "status IN ('waiting_for_payment', 'processing', 'shipped', 'delivered', 'cancelled')"
    )

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.alter_column('status',
            existing_type=sa.String(length=25),
            server_default='waiting_for_payment',
            existing_nullable=False)


def downgrade():
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.alter_column('status',
            existing_type=sa.String(length=25),
            server_default='waitingForPayment',
            existing_nullable=False)

    op.drop_constraint('ck_orders_status_valid', 'orders', type_='check')
    op.create_check_constraint(
        'ck_orders_status_valid',
        'orders',
        "status IN ('waitingForPayment', 'processing', 'shipped', 'delivered', 'cancelled')"
    )

    op.drop_table('order_items')

    op.create_table('order_items',
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name='fk_order_items_order_id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_order_items_product_id'),
        sa.PrimaryKeyConstraint('order_id', 'product_id')
    )
