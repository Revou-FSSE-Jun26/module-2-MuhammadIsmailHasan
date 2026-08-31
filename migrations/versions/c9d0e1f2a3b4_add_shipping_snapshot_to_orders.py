"""add shipping snapshot columns to orders

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-08-31

"""
from alembic import op
import sqlalchemy as sa


revision = 'c9d0e1f2a3b4'
down_revision = 'b8c9d0e1f2a3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('shipping_recipient_name', sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column('shipping_phone', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('shipping_address_line', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('shipping_city', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('shipping_postal_code', sa.String(length=20), nullable=True))


def downgrade():
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('shipping_postal_code')
        batch_op.drop_column('shipping_city')
        batch_op.drop_column('shipping_address_line')
        batch_op.drop_column('shipping_phone')
        batch_op.drop_column('shipping_recipient_name')
