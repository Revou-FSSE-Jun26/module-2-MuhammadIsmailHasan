from app.repositories.order_repository import OrderRepository


ALLOWED_TRANSITIONS = {
    'waiting_for_payment': ['processing', 'cancelled'],
    'processing': ['shipped', 'cancelled'],
    'shipped': ['delivered'],
    'delivered': [],
    'cancelled': [],
}

ROLE_ALLOWED_TARGET_STATUSES = {
    'buyer': set(),
    'seller': {'processing', 'shipped', 'delivered', 'cancelled'},
    'admin': {'waiting_for_payment', 'processing', 'shipped', 'delivered', 'cancelled'},
}

UNDELETABLE_STATUSES = ('shipped', 'delivered')


class OrderNotFoundError(Exception):
    pass


class OrderPermissionError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class InvalidStatusTransitionError(Exception):
    pass


class OrderCannotBeDeletedError(Exception):
    pass


class OrderService:

    @staticmethod
    def get_all(user_id=None, role=None, filters=None, sort_by='id', order='desc', page=1, limit=10):
        query_user_id = None if role == 'admin' else user_id

        return OrderRepository.get_all(
            user_id=query_user_id,
            filters=filters,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit,
        )

    @staticmethod
    def get_by_id(order_id, user_id=None, role=None):
        order = OrderRepository.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError("order not found")

        if role != 'admin' and order.user_id != user_id:
            raise OrderPermissionError("you don't have permission to view this order")

        return order

    @staticmethod
    def create(user_id, data):
        items_input = data['items']
        items_data = []

        for item in items_input:
            product = OrderRepository.get_product_by_id(item['product_id'])
            if not product:
                raise ProductNotFoundError(
                    f"product with id {item['product_id']} not found"
                )

            quantity = item['quantity']
            if product.stock < quantity:
                raise InsufficientStockError(
                    f"insufficient stock for product {product.name} "
                    f"(available: {product.stock}, requested: {quantity})"
                )

            unit_price = product.price
            sub_total = unit_price * quantity

            items_data.append({
                'product': product,
                'product_id': product.id,
                'unit_price': unit_price,
                'quantity': quantity,
                'sub_total': sub_total,
            })

        return OrderRepository.create(user_id, items_data)

    @staticmethod
    def update_status(order_id, data, user_id=None, role=None):
        order = OrderRepository.get_active_by_id(order_id)
        if not order:
            raise OrderNotFoundError("order not found")

        if role == 'admin':
            pass
        elif role == 'seller':
            if not OrderRepository.order_has_seller_product(order.id, user_id):
                raise OrderPermissionError(
                    "you don't have permission to update this order"
                )
        else:
            raise OrderPermissionError(
                "you don't have permission to update this order"
            )

        new_status = data['status']

        role_allowed = ROLE_ALLOWED_TARGET_STATUSES.get(role, set())
        if new_status not in role_allowed:
            raise OrderPermissionError(
                f"role '{role}' cannot set order status to '{new_status}'"
            )

        allowed = ALLOWED_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            raise InvalidStatusTransitionError(
                f"cannot change status from '{order.status}' to '{new_status}'"
            )

        return OrderRepository.update_status(order, new_status)

    @staticmethod
    def delete(order_id, user_id=None, role=None):
        order = OrderRepository.get_active_by_id(order_id)
        if not order:
            raise OrderNotFoundError("order not found")

        if role != 'admin' and order.user_id != user_id:
            raise OrderPermissionError("you don't have permission to delete this order")

        if order.status in UNDELETABLE_STATUSES:
            raise OrderCannotBeDeletedError(
                f"cannot delete order with status '{order.status}'"
            )

        refund_note = None

        if order.status == 'cancelled':
            OrderRepository.soft_delete(order)
        elif order.status in ('waiting_for_payment', 'processing'):
            if order.status == 'processing':
                refund_note = 'payment refund will be processed'
            OrderRepository.cancel_and_refund_stock(order)

        return order, refund_note
