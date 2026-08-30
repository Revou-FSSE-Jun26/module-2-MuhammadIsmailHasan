"""add user_profiles and user_addresses tables

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-08-31

"""
from alembic import op
import sqlalchemy as sa


revision = 'b8c9d0e1f2a3'
down_revision = 'a7b8c9d0e1f2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=True),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('avatar_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name='fk_user_profiles_user_id', ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_profiles_user_id'),
    )
    with op.batch_alter_table('user_profiles', schema=None) as batch_op:
        batch_op.create_index('ix_user_profiles_user_id', ['user_id'], unique=False)

    op.create_table(
        'user_addresses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=50), nullable=True),
        sa.Column('recipient_name', sa.String(length=150), nullable=False),
        sa.Column('phone', sa.String(length=30), nullable=False),
        sa.Column('address_line', sa.String(length=255), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name='fk_user_addresses_user_id', ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('user_addresses', schema=None) as batch_op:
        batch_op.create_index('ix_user_addresses_user_id', ['user_id'], unique=False)
        batch_op.create_index(
            'uq_user_addresses_one_default',
            ['user_id'],
            unique=True,
            sqlite_where=sa.text('is_default = 1'),
            postgresql_where=sa.text('is_default = true'),
        )


def downgrade():
    with op.batch_alter_table('user_addresses', schema=None) as batch_op:
        batch_op.drop_index('uq_user_addresses_one_default')
        batch_op.drop_index('ix_user_addresses_user_id')
    op.drop_table('user_addresses')

    with op.batch_alter_table('user_profiles', schema=None) as batch_op:
        batch_op.drop_index('ix_user_profiles_user_id')
    op.drop_table('user_profiles')
