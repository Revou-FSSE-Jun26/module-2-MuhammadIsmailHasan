from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import jsonify, current_app
from flask_jwt_extended import get_jwt_identity

from app.schemas.cart_schema import (
    AddCartItemSchema,
    UpdateCartItemSchema,
    CheckoutSchema,
)
from app.schemas.order_schema import OrderDetailResponseSchema
from app.services.cart_service import (
    CartService,
    ProductNotFoundError,
    CartItemNotFoundError,
    InsufficientStockError,
    EmptyCartError,
    ProductUnavailableError,
    CartSelectionError,
)
from app.services.order_service import (
    ProductNotFoundError as OrderProductNotFoundError,
    InsufficientStockError as OrderInsufficientStockError,
)
from app.auth import roles_required

cart_blp = Blueprint(
    'cart',
    __name__,
    url_prefix='/api/v1/cart',
    description='Shopping cart operations',
)


@cart_blp.route('')
class CartResource(MethodView):

    @roles_required('buyer', 'admin')
    def get(self):
        current_user_id = int(get_jwt_identity())
        cart = CartService.get_cart(current_user_id)

        return jsonify({
            'message': 'get cart success',
            'status': True,
            'data': cart,
        }), 200

    @roles_required('buyer', 'admin')
    def delete(self):
        current_user_id = int(get_jwt_identity())
        cart = CartService.clear_cart(current_user_id)

        return jsonify({
            'message': 'cart cleared',
            'status': True,
            'data': cart,
        }), 200


@cart_blp.route('/items')
class CartItemList(MethodView):

    @cart_blp.arguments(AddCartItemSchema)
    @roles_required('buyer', 'admin')
    def post(self, validated_data):
        current_user_id = int(get_jwt_identity())

        try:
            cart = CartService.add_item(
                current_user_id,
                validated_data['product_id'],
                validated_data['quantity'],
            )
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except InsufficientStockError as e:
            abort(422, message=str(e))

        return jsonify({
            'message': 'item added to cart',
            'status': True,
            'data': cart,
        }), 201


@cart_blp.route('/items/<int:item_id>')
class CartItemResource(MethodView):

    @cart_blp.arguments(UpdateCartItemSchema)
    @roles_required('buyer', 'admin')
    def put(self, validated_data, item_id):
        current_user_id = int(get_jwt_identity())

        try:
            cart = CartService.update_item(
                current_user_id, item_id, validated_data['quantity']
            )
        except CartItemNotFoundError as e:
            abort(404, message=str(e))
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except InsufficientStockError as e:
            abort(422, message=str(e))

        return jsonify({
            'message': 'cart item updated',
            'status': True,
            'data': cart,
        }), 200

    @roles_required('buyer', 'admin')
    def delete(self, item_id):
        current_user_id = int(get_jwt_identity())

        try:
            cart = CartService.remove_item(current_user_id, item_id)
        except CartItemNotFoundError as e:
            abort(404, message=str(e))

        return jsonify({
            'message': 'cart item removed',
            'status': True,
            'data': cart,
        }), 200


@cart_blp.route('/checkout')
class CartCheckout(MethodView):

    @cart_blp.arguments(CheckoutSchema)
    @roles_required('buyer', 'admin')
    def post(self, validated_data):
        current_user_id = int(get_jwt_identity())

        try:
            order = CartService.checkout(
                current_user_id,
                seller_id=validated_data.get('seller_id'),
                cart_item_ids=validated_data.get('cart_item_ids'),
            )
        except EmptyCartError as e:
            abort(400, message=str(e))
        except CartSelectionError as e:
            abort(404, message=str(e))
        except ProductUnavailableError as e:
            abort(409, message=str(e))
        except (InsufficientStockError, OrderInsufficientStockError) as e:
            abort(422, message=str(e))
        except (ProductNotFoundError, OrderProductNotFoundError) as e:
            abort(404, message=str(e))

        current_app.logger.info(
            'order %s placed via cart checkout by user %s', order.id, current_user_id
        )

        return jsonify({
            'message': 'checkout success',
            'status': True,
            'data': OrderDetailResponseSchema().dump(order),
        }), 201
