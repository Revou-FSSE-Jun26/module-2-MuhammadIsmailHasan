"""add image to categories and sub_categories

Revision ID: f1a2b3c4d5e6
Revises: e943a5f882e7
Create Date: 2026-10-16

"""
from alembic import op
import sqlalchemy as sa


revision = 'f1a2b3c4d5e6'
down_revision = 'e943a5f882e7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image', sa.String(length=500), nullable=True))

    with op.batch_alter_table('sub_categories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image', sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table('sub_categories', schema=None) as batch_op:
        batch_op.drop_column('image')

    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_column('image')
