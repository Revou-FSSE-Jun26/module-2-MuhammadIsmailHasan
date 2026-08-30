from sqlalchemy.orm import selectinload

from app.models.carts import Cart, CartItem
from app.models.products import Product
from app.extensions import db


class CartRepository:

    _cart_load = (
        selectinload(Cart.items)
        .selectinload(CartItem.product)
        .options(
            selectinload(Product.images),
            selectinload(Product.seller),
        )
    )

    @staticmethod
    def get_active_cart(user_id):
        return (
            Cart.query
            .options(CartRepository._cart_load)
            .filter_by(user_id=user_id, is_active=True)
            .first()
        )

    @staticmethod
    def get_or_create_cart(user_id):
        cart = Cart.query.filter_by(user_id=user_id, is_active=True).first()
        if cart:
            return cart

        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()
        return cart

    @staticmethod
    def get_item(cart_id, item_id):
        return CartItem.query.filter_by(id=item_id, cart_id=cart_id).first()

    @staticmethod
    def get_item_by_product(cart_id, product_id):
        return CartItem.query.filter_by(cart_id=cart_id, product_id=product_id).first()

    @staticmethod
    def get_product(product_id):
        return Product.query.filter_by(id=product_id, is_active=True).first()

    @staticmethod
    def add_item(cart_id, product_id, quantity):
        item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity)
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def set_quantity(item, quantity):
        item.quantity = quantity
        db.session.commit()
        return item

    @staticmethod
    def delete_item(item):
        db.session.delete(item)
        db.session.commit()

    @staticmethod
    def clear_items(cart):
        for item in list(cart.items):
            db.session.delete(item)
        db.session.commit()
        return cart

    @staticmethod
    def delete_items_by_product_ids(cart, product_ids):
        target = set(product_ids)
        for item in list(cart.items):
            if item.product_id in target:
                db.session.delete(item)
        db.session.commit()
        return cart
