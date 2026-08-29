"""add updated_by to orders

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-29

"""
from alembic import op
import sqlalchemy as sa


revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('updated_by', sa.Integer(), nullable=True))
        batch_op.create_index('ix_orders_updated_by', ['updated_by'], unique=False)
        batch_op.create_foreign_key(
            'fk_orders_updated_by',
            'users',
            ['updated_by'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade():
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_constraint('fk_orders_updated_by', type_='foreignkey')
        batch_op.drop_index('ix_orders_updated_by')
        batch_op.drop_column('updated_by')
