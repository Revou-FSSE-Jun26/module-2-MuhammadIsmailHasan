"""add seller_id to products

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-29

"""
from alembic import op
import sqlalchemy as sa


revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('seller_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_products_seller_id', ['seller_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_products_seller_id',
            'users',
            ['seller_id'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_constraint('fk_products_seller_id', type_='foreignkey')
        batch_op.drop_index('ix_products_seller_id')
        batch_op.drop_column('seller_id')
