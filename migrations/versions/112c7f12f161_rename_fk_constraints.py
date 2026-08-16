"""rename fk constraints

Revision ID: 112c7f12f161
Revises: e67349ef02fb
Create Date: 2026-08-16

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '112c7f12f161'
down_revision = 'e67349ef02fb'
branch_labels = None
depends_on = None


def upgrade():
    # Products: rename category_id FK
    op.drop_constraint('products_category_id_fkey', 'products', type_='foreignkey')
    op.create_foreign_key('fk_products_category_id', 'products', 'categories', ['category_id'], ['id'], ondelete='SET NULL')

    # Orders: rename user_id FK
    op.drop_constraint('orders_user_id_fkey', 'orders', type_='foreignkey')
    op.create_foreign_key('fk_orders_user_id', 'orders', 'users', ['user_id'], ['id'], ondelete='RESTRICT')

    # Order items: rename order_id FK
    op.drop_constraint('order_items_order_id_fkey', 'order_items', type_='foreignkey')
    op.create_foreign_key('fk_order_items_order_id', 'order_items', 'orders', ['order_id'], ['id'])

    # Order items: rename product_id FK
    op.drop_constraint('order_items_product_id_fkey', 'order_items', type_='foreignkey')
    op.create_foreign_key('fk_order_items_product_id', 'order_items', 'products', ['product_id'], ['id'])


def downgrade():
    # Order items: revert product_id FK
    op.drop_constraint('fk_order_items_product_id', 'order_items', type_='foreignkey')
    op.create_foreign_key('order_items_product_id_fkey', 'order_items', 'products', ['product_id'], ['id'])

    # Order items: revert order_id FK
    op.drop_constraint('fk_order_items_order_id', 'order_items', type_='foreignkey')
    op.create_foreign_key('order_items_order_id_fkey', 'order_items', 'orders', ['order_id'], ['id'])

    # Orders: revert user_id FK
    op.drop_constraint('fk_orders_user_id', 'orders', type_='foreignkey')
    op.create_foreign_key('orders_user_id_fkey', 'orders', 'users', ['user_id'], ['id'], ondelete='RESTRICT')

    # Products: revert category_id FK
    op.drop_constraint('fk_products_category_id', 'products', type_='foreignkey')
    op.create_foreign_key('products_category_id_fkey', 'products', 'categories', ['category_id'], ['id'], ondelete='SET NULL')
