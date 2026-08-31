from decimal import Decimal

from app.repositories.cart_repository import CartRepository
from app.services.order_service import OrderService


class ProductNotFoundError(Exception):
    pass


class CartItemNotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class EmptyCartError(Exception):
    pass


class ProductUnavailableError(Exception):
    pass


class CartSelectionError(Exception):
    pass


class CartService:

    @staticmethod
    def get_cart(user_id):
        cart = CartRepository.get_active_cart(user_id)
        return CartService._build_cart_view(cart)

    @staticmethod
    def add_item(user_id, product_id, quantity):
        product = CartRepository.get_product(product_id)
        if not product:
            raise ProductNotFoundError("product not found")

        cart = CartRepository.get_or_create_cart(user_id)
        existing = CartRepository.get_item_by_product(cart.id, product_id)

        new_quantity = quantity + (existing.quantity if existing else 0)

        if product.stock < new_quantity:
            raise InsufficientStockError(
                f"insufficient stock for product {product.name} "
                f"(available: {product.stock}, requested: {new_quantity})"
            )

        if existing:
            CartRepository.set_quantity(existing, new_quantity)
        else:
            CartRepository.add_item(cart.id, product_id, quantity)

        return CartService.get_cart(user_id)

    @staticmethod
    def update_item(user_id, item_id, quantity):
        cart = CartRepository.get_active_cart(user_id)
        if not cart:
            raise CartItemNotFoundError("cart item not found")

        item = CartRepository.get_item(cart.id, item_id)
        if not item:
            raise CartItemNotFoundError("cart item not found")

        if quantity <= 0:
            CartRepository.delete_item(item)
            return CartService.get_cart(user_id)

        product = CartRepository.get_product(item.product_id)
        if not product:
            raise ProductNotFoundError("product not found")

        if product.stock < quantity:
            raise InsufficientStockError(
                f"insufficient stock for product {product.name} "
                f"(available: {product.stock}, requested: {quantity})"
            )

        CartRepository.set_quantity(item, quantity)
        return CartService.get_cart(user_id)

    @staticmethod
    def remove_item(user_id, item_id):
        cart = CartRepository.get_active_cart(user_id)
        if not cart:
            raise CartItemNotFoundError("cart item not found")

        item = CartRepository.get_item(cart.id, item_id)
        if not item:
            raise CartItemNotFoundError("cart item not found")

        CartRepository.delete_item(item)
        return CartService.get_cart(user_id)

    @staticmethod
    def clear_cart(user_id):
        cart = CartRepository.get_active_cart(user_id)
        if cart:
            CartRepository.clear_items(cart)
        return CartService.get_cart(user_id)

    @staticmethod
    def _select_items(cart, seller_id=None, cart_item_ids=None):
        if cart_item_ids is not None:
            by_id = {item.id: item for item in cart.items}
            unknown = [iid for iid in cart_item_ids if iid not in by_id]
            if unknown:
                raise CartSelectionError(
                    f"cart items not found: {', '.join(str(i) for i in unknown)}"
                )
            wanted = set(cart_item_ids)
            return [item for item in cart.items if item.id in wanted]

        if seller_id is not None:
            selected = [
                item for item in cart.items
                if item.product and item.product.seller_id == seller_id
            ]
            if not selected:
                raise CartSelectionError(
                    f"no cart items found for seller {seller_id}"
                )
            return selected

        return list(cart.items)

    @staticmethod
    def checkout(user_id, seller_id=None, cart_item_ids=None, address_id=None):
        cart = CartRepository.get_active_cart(user_id)
        if not cart or not cart.items:
            raise EmptyCartError("cart is empty")

        selected = CartService._select_items(cart, seller_id, cart_item_ids)
        if not selected:
            raise EmptyCartError("cart is empty")

        items_payload = []
        ordered_product_ids = []
        for item in selected:
            product = item.product
            if not product or not product.is_active:
                name = product.name if product else f"id {item.product_id}"
                raise ProductUnavailableError(
                    f"product {name} is no longer available; remove it to continue"
                )
            if product.stock < item.quantity:
                raise InsufficientStockError(
                    f"insufficient stock for product {product.name} "
                    f"(available: {product.stock}, requested: {item.quantity})"
                )
            items_payload.append({'product_id': item.product_id, 'quantity': item.quantity})
            ordered_product_ids.append(item.product_id)

        order = OrderService.create(
            user_id, {'items': items_payload, 'address_id': address_id}
        )

        CartRepository.delete_items_by_product_ids(cart, ordered_product_ids)

        return order

    @staticmethod
    def _build_item_view(item):
        product = item.product
        available = bool(product and product.is_active)
        in_stock = bool(product and product.stock >= item.quantity)

        unit_price = float(product.price) if product and product.price is not None else None
        sub_total = (
            float(Decimal(str(product.price)) * item.quantity)
            if product and product.price is not None else None
        )
        primary = product.primary_image if product else None

        note = None
        if not available:
            note = 'product is no longer available'
        elif not in_stock:
            note = f'only {product.stock} left in stock'

        return {
            'id': item.id,
            'product_id': item.product_id,
            'quantity': item.quantity,
            'unit_price': unit_price,
            'sub_total': sub_total,
            'available': available and in_stock,
            'note': note,
            'product': {
                'id': product.id if product else None,
                'name': product.name if product else None,
                'slug': product.slug if product else None,
                'price': unit_price,
                'stock': product.stock if product else None,
                'is_active': product.is_active if product else None,
                'image': primary.url if primary else None,
            } if product else None,
        }

    @staticmethod
    def _build_cart_view(cart):
        if not cart:
            return {
                'cart_id': None,
                'groups': [],
                'total_items': 0,
                'total_quantity': 0,
                'grand_total': 0.0,
            }

        groups = {}
        group_order = []

        for item in cart.items:
            product = item.product
            seller_id = product.seller_id if product else None
            seller_name = (
                product.seller.username
                if product and product.seller else None
            )

            if seller_id not in groups:
                groups[seller_id] = {
                    'seller_id': seller_id,
                    'seller_name': seller_name or 'Unknown seller',
                    'items': [],
                    'group_total_items': 0,
                    'group_total_quantity': 0,
                    'group_total': 0.0,
                }
                group_order.append(seller_id)

            item_view = CartService._build_item_view(item)
            group = groups[seller_id]
            group['items'].append(item_view)
            group['group_total_items'] += 1
            group['group_total_quantity'] += item.quantity
            if item_view['sub_total'] is not None:
                group['group_total'] += item_view['sub_total']

        grouped = [groups[sid] for sid in group_order]

        total_items = sum(g['group_total_items'] for g in grouped)
        total_quantity = sum(g['group_total_quantity'] for g in grouped)
        grand_total = sum(g['group_total'] for g in grouped)
        for g in grouped:
            g['group_total'] = round(g['group_total'], 2)

        return {
            'cart_id': cart.id,
            'groups': grouped,
            'total_items': total_items,
            'total_quantity': total_quantity,
            'grand_total': round(grand_total, 2),
        }
