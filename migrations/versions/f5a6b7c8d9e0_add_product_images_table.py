"""add product_images table

Revision ID: f5a6b7c8d9e0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-30

"""
from alembic import op
import sqlalchemy as sa


revision = 'f5a6b7c8d9e0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'product_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint('"order" >= 0', name='ck_product_images_order_non_negative'),
        sa.ForeignKeyConstraint(
            ['product_id'], ['products.id'],
            name='fk_product_images_product_id', ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('product_images', schema=None) as batch_op:
        batch_op.create_index('ix_product_images_product_id', ['product_id'], unique=False)
        batch_op.create_index(
            'ix_product_images_product_id_order', ['product_id', 'order'], unique=False
        )


def downgrade():
    with op.batch_alter_table('product_images', schema=None) as batch_op:
        batch_op.drop_index('ix_product_images_product_id_order')
        batch_op.drop_index('ix_product_images_product_id')
    op.drop_table('product_images')
