"""add carts and cart_items tables

Revision ID: a7b8c9d0e1f2
Revises: f5a6b7c8d9e0
Create Date: 2026-08-30

"""
from alembic import op
import sqlalchemy as sa


revision = 'a7b8c9d0e1f2'
down_revision = 'f5a6b7c8d9e0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'carts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name='fk_carts_user_id', ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_carts_user_id'),
    )
    with op.batch_alter_table('carts', schema=None) as batch_op:
        batch_op.create_index('ix_carts_user_id', ['user_id'], unique=False)

    op.create_table(
        'cart_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cart_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint('quantity > 0', name='ck_cart_items_quantity_positive'),
        sa.ForeignKeyConstraint(
            ['cart_id'], ['carts.id'],
            name='fk_cart_items_cart_id', ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['product_id'], ['products.id'],
            name='fk_cart_items_product_id', ondelete='RESTRICT',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cart_id', 'product_id', name='uq_cart_items_cart_product'),
    )
    with op.batch_alter_table('cart_items', schema=None) as batch_op:
        batch_op.create_index('ix_cart_items_cart_id', ['cart_id'], unique=False)
        batch_op.create_index('ix_cart_items_product_id', ['product_id'], unique=False)


def downgrade():
    with op.batch_alter_table('cart_items', schema=None) as batch_op:
        batch_op.drop_index('ix_cart_items_product_id')
        batch_op.drop_index('ix_cart_items_cart_id')
    op.drop_table('cart_items')

    with op.batch_alter_table('carts', schema=None) as batch_op:
        batch_op.drop_index('ix_carts_user_id')
    op.drop_table('carts')
