from app.repositories.order_repository import OrderRepository


ALLOWED_TRANSITIONS = {
    'waiting_for_payment': ['processing', 'cancelled'],
    'processing': ['shipped', 'cancelled'],
    'shipped': ['delivered'],
    'delivered': [],
    'cancelled': [],
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
        """
        Get paginated orders. Admin sees all, others see only their own.
        """
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
        """
        Get order by ID with ownership check.
        Admin can view any order, others can only view their own.
        """
        order = OrderRepository.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError("order not found")

        if role != 'admin' and order.user_id != user_id:
            raise OrderPermissionError("you don't have permission to view this order")

        return order

    @staticmethod
    def create(user_id, data):
        """
        Create an order:
        1. Validate each product exists and is active
        2. Check stock availability
        3. Calculate unit_price and sub_total
        4. Create order with items and deduct stock
        """
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
        """
        Update order status with ownership check and transition validation.
        """
        order = OrderRepository.get_active_by_id(order_id)
        if not order:
            raise OrderNotFoundError("order not found")

        if role != 'admin' and order.user_id != user_id:
            raise OrderPermissionError("you don't have permission to update this order")

        new_status = data['status']
        allowed = ALLOWED_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            raise InvalidStatusTransitionError(
                f"cannot change status from '{order.status}' to '{new_status}'"
            )

        return OrderRepository.update_status(order, new_status)

    @staticmethod
    def delete(order_id, user_id=None, role=None):
        """
        Delete (cancel) an order:
        - Cannot delete shipped or delivered orders
        - If status is 'cancelled', just soft-delete
        - If status is 'waiting_for_payment' or 'processing', cancel + refund stock
        - Returns refund_note if order was in 'processing' status

        Returns:
            tuple: (order, refund_note or None)
        """
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
