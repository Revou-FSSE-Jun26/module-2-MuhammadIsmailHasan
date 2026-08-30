from sqlalchemy.orm import selectinload

from app.models.orders import Order, OrderItem
from app.models.products import Product
from app.models.product_images import ProductImage
from app.extensions import db
from decimal import Decimal


class OrderRepository:

    _detail_load = selectinload(Order.items).selectinload(OrderItem.product).selectinload(Product.images)
    _items_load = selectinload(Order.items)

    @staticmethod
    def get_all(user_id=None, seller_id=None, filters=None, sort_by='id', order='desc', page=1, limit=10):
        query = Order.query.options(OrderRepository._items_load)

        if user_id is not None:
            query = query.filter_by(user_id=user_id)

        if seller_id is not None:
            query = query.join(
                OrderItem, OrderItem.order_id == Order.id
            ).join(
                Product, OrderItem.product_id == Product.id
            ).filter(
                Product.seller_id == seller_id
            ).distinct()

        if filters:
            include_deleted = filters.get('include_deleted', False)
            if not include_deleted:
                query = query.filter(Order.is_active == True)

            if filters.get('status'):
                query = query.filter(Order.status == filters['status'])

        sort_columns = {
            'id': Order.id,
            'total_amount': Order.total_amount,
            'ordered_at': Order.ordered_at,
        }
        sort_column = sort_columns.get(sort_by, Order.id)

        if order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        return query.paginate(page=page, per_page=limit, error_out=False)

    @staticmethod
    def get_by_id(order_id):
        return (
            Order.query
            .options(OrderRepository._detail_load)
            .filter_by(id=order_id)
            .first()
        )

    @staticmethod
    def get_active_by_id(order_id):
        return Order.query.filter_by(id=order_id, is_active=True).first()

    @staticmethod
    def create(user_id, items_data):
        total_amount = sum(item['sub_total'] for item in items_data)

        order = Order(
            user_id=user_id,
            total_amount=total_amount,
        )
        db.session.add(order)
        db.session.flush()

        for item_data in items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                unit_price=item_data['unit_price'],
                quantity=item_data['quantity'],
                sub_total=item_data['sub_total'],
            )
            db.session.add(order_item)
            item_data['product'].stock -= item_data['quantity']

        db.session.commit()
        return order

    @staticmethod
    def update_status(order, new_status, updated_by=None):
        order.status = new_status
        order.updated_by = updated_by
        db.session.commit()
        return order

    @staticmethod
    def cancel_order(order, updated_by=None):
        order.status = 'cancelled'
        order.is_active = False
        order.updated_by = updated_by

        for item in order.items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock += item.quantity

        db.session.commit()
        return order

    @staticmethod
    def get_product_by_id(product_id):
        return Product.query.filter_by(id=product_id, is_active=True).first()

    @staticmethod
    def order_has_seller_product(order_id, seller_id):
        exists = db.session.query(OrderItem.id).join(
            Product, OrderItem.product_id == Product.id
        ).filter(
            OrderItem.order_id == order_id,
            Product.seller_id == seller_id,
        ).first()

        return exists is not None
