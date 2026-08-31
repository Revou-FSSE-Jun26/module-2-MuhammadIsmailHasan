from app.repositories.order_repository import OrderRepository
from app.repositories.user_address_repository import UserAddressRepository
from app.validation import (
    ALLOWED_TRANSITIONS,
    ROLE_ALLOWED_TARGET_STATUSES,
    UNDELETABLE_STATUSES,
    TERMINAL_STATUSES,
)


class OrderNotFoundError(Exception):
    pass


class ShippingAddressRequiredError(Exception):
    pass


class AddressNotFoundError(Exception):
    pass


class AddressChangeNotAllowedError(Exception):
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


class TrackingIdRequiredError(Exception):
    pass


class OrderService:

    @staticmethod
    def get_all(user_id=None, role=None, filters=None, sort_by='id', order='desc', page=1, limit=10):
        query_user_id = None
        query_seller_id = None

        if role == 'admin':
            pass
        elif role == 'seller':
            query_seller_id = user_id
        else:
            query_user_id = user_id

        return OrderRepository.get_all(
            user_id=query_user_id,
            seller_id=query_seller_id,
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

        if role == 'admin':
            return order

        if role == 'seller':
            if not OrderRepository.order_has_seller_product(order.id, user_id):
                raise OrderPermissionError("you don't have permission to view this order")
            return order

        if order.user_id != user_id:
            raise OrderPermissionError("you don't have permission to view this order")

        return order

    @staticmethod
    def _resolve_shipping_address(user_id, address_id=None):
        if address_id is not None:
            address = UserAddressRepository.get(user_id, address_id)
            if not address:
                raise AddressNotFoundError("address not found")
        else:
            address = UserAddressRepository.get_default(user_id)
            if not address:
                raise ShippingAddressRequiredError(
                    "a shipping address is required to place an order"
                )

        return {
            'shipping_recipient_name': address.recipient_name,
            'shipping_phone': address.phone,
            'shipping_address_line': address.address_line,
            'shipping_city': address.city,
            'shipping_postal_code': address.postal_code,
        }

    @staticmethod
    def create(user_id, data):
        shipping = OrderService._resolve_shipping_address(
            user_id, data.get('address_id')
        )

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

        return OrderRepository.create(user_id, items_data, shipping)

    @staticmethod
    def change_address(order_id, address_id, user_id):
        order = OrderRepository.get_by_id(order_id)
        if not order or not order.is_active:
            raise OrderNotFoundError("order not found")

        if order.user_id != user_id:
            raise OrderPermissionError(
                "you don't have permission to change this order's address"
            )

        if order.status != 'waiting_for_payment':
            raise AddressChangeNotAllowedError(
                f"shipping address can no longer be changed for a "
                f"'{order.status}' order"
            )

        shipping = OrderService._resolve_shipping_address(user_id, address_id)
        return OrderRepository.update_shipping(order, shipping)

    @staticmethod
    def update_status(order_id, data, user_id=None, role=None):
        order = OrderRepository.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError("order not found")

        if order.status in TERMINAL_STATUSES or not order.is_active:
            raise InvalidStatusTransitionError(
                f"order is '{order.status}' and can no longer be modified"
            )

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

        tracking_id = None
        if new_status == 'shipped':
            tracking_id = data.get('tracking_id')
            if not tracking_id:
                raise TrackingIdRequiredError(
                    "tracking_id is required to mark an order as shipped"
                )

        return OrderRepository.update_status(
            order, new_status, updated_by=user_id, tracking_id=tracking_id
        )

    @staticmethod
    def cancel(order_id, user_id=None, role=None):
        order = OrderRepository.get_active_by_id(order_id)
        if not order:
            raise OrderNotFoundError("order not found")

        if role == 'admin':
            pass
        elif role == 'seller':
            if not OrderRepository.order_has_seller_product(order.id, user_id):
                raise OrderPermissionError("you don't have permission to cancel this order")
        elif order.user_id != user_id:
            raise OrderPermissionError("you don't have permission to cancel this order")

        if order.status in UNDELETABLE_STATUSES:
            raise OrderCannotBeDeletedError(
                f"cannot cancel order with status '{order.status}'"
            )

        refund_note = None
        if order.status == 'processing':
            refund_note = 'payment refund will be processed'

        OrderRepository.cancel_order(order, updated_by=user_id)

        return order, refund_note
