"""add sub_categories

Revision ID: e943a5f882e7
Revises: e14203fe5a28
Create Date: 2026-10-16

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e943a5f882e7"
down_revision = "e14203fe5a28"
branch_labels = None
depends_on = None


def upgrade():
    # (a) create sub_categories table
    op.create_table(
        "sub_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name="fk_sub_categories_category_id",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_sub_categories_name"),
    )
    op.create_index(
        "ix_sub_categories_category_id", "sub_categories", ["category_id"], unique=False
    )

    # (b) add products.sub_category_id with its index + FK
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.add_column(sa.Column("sub_category_id", sa.Integer(), nullable=True))
        batch_op.create_index(
            "ix_products_sub_category_id", ["sub_category_id"], unique=False
        )
        batch_op.create_foreign_key(
            "fk_products_sub_category_id",
            "sub_categories",
            ["sub_category_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # (c) data backfill: for every distinct category referenced by a product,
    # create a sub-category (named after the category) and relink the products.
    bind = op.get_bind()

    categories = sa.table(
        "categories",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
    )
    sub_categories = sa.table(
        "sub_categories",
        sa.column("id", sa.Integer),
        sa.column("category_id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("is_active", sa.Boolean),
    )
    products = sa.table(
        "products",
        sa.column("id", sa.Integer),
        sa.column("category_id", sa.Integer),
        sa.column("sub_category_id", sa.Integer),
    )

    distinct_category_ids = [
        row[0]
        for row in bind.execute(
            sa.select(products.c.category_id)
            .where(products.c.category_id.isnot(None))
            .distinct()
        )
    ]

    for category_id in distinct_category_ids:
        cat_name = bind.execute(
            sa.select(categories.c.name).where(categories.c.id == category_id)
        ).scalar()
        if cat_name is None:
            cat_name = "General"

        # keep the sub-category name unique across the whole table by
        # suffixing with the originating category id.
        sub_name = f"{cat_name} ({category_id})"

        bind.execute(
            sub_categories.insert().values(
                category_id=category_id,
                name=sub_name,
                is_active=True,
            )
        )
        # fetch the id back by its (unique) name — portable across SQLite/PG
        new_sub_id = bind.execute(
            sa.select(sub_categories.c.id).where(sub_categories.c.name == sub_name)
        ).scalar()

        bind.execute(
            products.update()
            .where(products.c.category_id == category_id)
            .values(sub_category_id=new_sub_id)
        )

    # (d) drop the old products.category_id FK, index and column
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.drop_constraint("fk_products_category_id", type_="foreignkey")
        try:
            batch_op.drop_index("ix_products_category_id")
        except Exception:
            pass
        batch_op.drop_column("category_id")


def downgrade():
    # re-add products.category_id with its index + FK
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.add_column(sa.Column("category_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_products_category_id", ["category_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_products_category_id",
            "categories",
            ["category_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # backfill category_id from the parent category of each sub-category
    bind = op.get_bind()

    sub_categories = sa.table(
        "sub_categories",
        sa.column("id", sa.Integer),
        sa.column("category_id", sa.Integer),
    )
    products = sa.table(
        "products",
        sa.column("id", sa.Integer),
        sa.column("category_id", sa.Integer),
        sa.column("sub_category_id", sa.Integer),
    )

    sub_rows = bind.execute(
        sa.select(sub_categories.c.id, sub_categories.c.category_id)
    ).fetchall()

    for sub_id, parent_category_id in sub_rows:
        bind.execute(
            products.update()
            .where(products.c.sub_category_id == sub_id)
            .values(category_id=parent_category_id)
        )

    # drop products.sub_category_id FK, index and column
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.drop_constraint("fk_products_sub_category_id", type_="foreignkey")
        try:
            batch_op.drop_index("ix_products_sub_category_id")
        except Exception:
            pass
        batch_op.drop_column("sub_category_id")

    op.drop_index("ix_sub_categories_category_id", table_name="sub_categories")
    op.drop_table("sub_categories")
