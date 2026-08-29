"""add slug to products

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-29

"""
import re
import unicodedata

from alembic import op
import sqlalchemy as sa


revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def _slugify(value):
    if value is None:
        return 'product'
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = value.lower().strip()
    value = re.sub(r'[^a-z0-9]+', '-', value).strip('-')
    return value or 'product'


def upgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=300), nullable=True))

    # Backfill existing rows with unique slugs derived from name.
    conn = op.get_bind()
    rows = conn.execute(sa.text('SELECT id, name FROM products ORDER BY id')).fetchall()

    used = set()
    for row in rows:
        base = _slugify(row.name)
        candidate = base
        suffix = 2
        while candidate in used:
            candidate = f'{base}-{suffix}'
            suffix += 1
        used.add(candidate)
        conn.execute(
            sa.text('UPDATE products SET slug = :slug WHERE id = :id'),
            {'slug': candidate, 'id': row.id},
        )

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.alter_column('slug', existing_type=sa.String(length=300), nullable=False)
        batch_op.create_index('ix_products_slug', ['slug'], unique=True)


def downgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_index('ix_products_slug')
        batch_op.drop_column('slug')
