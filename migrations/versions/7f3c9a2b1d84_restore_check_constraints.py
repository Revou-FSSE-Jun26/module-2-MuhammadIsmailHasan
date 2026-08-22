"""restore check constraints and add unique constraint on categories.name

Migration e67349ef02fb dropped three CHECK constraints from the database and
only recreated them in its downgrade(), so they were lost permanently. The
models still declared them, which left the models and the database out of sync.

Alembic's autogenerate does not compare CHECK constraints, so this drift is
invisible to `flask db migrate` and has to be written by hand.

Note the price rule changed deliberately. The original constraint was
`price > 0`; it is now `price >= 0` so a seller can list a free giveaway item.

Revision ID: 7f3c9a2b1d84
Revises: 31dbd40318fe
Create Date: 2026-08-22

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '7f3c9a2b1d84'
down_revision = '31dbd40318fe'
branch_labels = None
depends_on = None


ORDER_STATUSES = (
    'waitingForPayment',
    'processing',
    'shipped',
    'delivered',
    'cancelled',
)

STATUS_CONDITION = 'status IN (%s)' % ', '.join(
    "'%s'" % status for status in ORDER_STATUSES
)


def upgrade():
    op.create_check_constraint(
        'ck_products_price_non_negative',
        'products',
        'price >= 0',
    )

    op.create_check_constraint(
        'ck_orders_total_amount_non_negative',
        'orders',
        'total_amount >= 0',
    )

    op.create_check_constraint(
        'ck_orders_status_valid',
        'orders',
        STATUS_CONDITION,
    )

    op.create_unique_constraint(
        'uq_categories_name',
        'categories',
        ['name'],
    )


def downgrade():
    op.drop_constraint('uq_categories_name', 'categories', type_='unique')
    op.drop_constraint('ck_orders_status_valid', 'orders', type_='check')
    op.drop_constraint('ck_orders_total_amount_non_negative', 'orders', type_='check')
    op.drop_constraint('ck_products_price_non_negative', 'products', type_='check')
