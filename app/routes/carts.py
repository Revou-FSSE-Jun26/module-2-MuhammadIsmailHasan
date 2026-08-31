from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import current_app

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
    ShippingAddressRequiredError,
    AddressNotFoundError,
)
from app.auth import roles_required
from app.utils.auth_context import current_user_id
from app.utils.http import make_response

cart_blp = Blueprint(
    'cart',
    __name__,
    url_prefix='/api/v1/cart',
    description='Shopping cart operations',
)


@cart_blp.route('')
class CartResource(MethodView):

    @roles_required('buyer')
    def get(self):
        cart = CartService.get_cart(current_user_id())
        return make_response('get cart success', cart)

    @roles_required('buyer')
    def delete(self):
        cart = CartService.clear_cart(current_user_id())
        return make_response('cart cleared', cart)


@cart_blp.route('/items')
class CartItemList(MethodView):

    @cart_blp.arguments(AddCartItemSchema)
    @roles_required('buyer')
    def post(self, validated_data):
        try:
            cart = CartService.add_item(
                current_user_id(),
                validated_data['product_id'],
                validated_data['quantity'],
            )
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except InsufficientStockError as e:
            abort(422, message=str(e))

        return make_response('item added to cart', cart, 201)


@cart_blp.route('/items/<int:item_id>')
class CartItemResource(MethodView):

    @cart_blp.arguments(UpdateCartItemSchema)
    @roles_required('buyer')
    def put(self, validated_data, item_id):
        try:
            cart = CartService.update_item(
                current_user_id(), item_id, validated_data['quantity']
            )
        except CartItemNotFoundError as e:
            abort(404, message=str(e))
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except InsufficientStockError as e:
            abort(422, message=str(e))

        return make_response('cart item updated', cart)

    @roles_required('buyer')
    def delete(self, item_id):
        try:
            cart = CartService.remove_item(current_user_id(), item_id)
        except CartItemNotFoundError as e:
            abort(404, message=str(e))

        return make_response('cart item removed', cart)


@cart_blp.route('/checkout')
class CartCheckout(MethodView):

    @cart_blp.arguments(CheckoutSchema)
    @roles_required('buyer')
    def post(self, validated_data):
        user_id = current_user_id()

        try:
            order = CartService.checkout(
                user_id,
                seller_id=validated_data.get('seller_id'),
                cart_item_ids=validated_data.get('cart_item_ids'),
                address_id=validated_data.get('address_id'),
            )
        except EmptyCartError as e:
            abort(400, message=str(e))
        except CartSelectionError as e:
            abort(404, message=str(e))
        except AddressNotFoundError as e:
            abort(404, message=str(e))
        except ShippingAddressRequiredError as e:
            abort(422, message=str(e))
        except ProductUnavailableError as e:
            abort(409, message=str(e))
        except (InsufficientStockError, OrderInsufficientStockError) as e:
            abort(422, message=str(e))
        except (ProductNotFoundError, OrderProductNotFoundError) as e:
            abort(404, message=str(e))

        current_app.logger.info(
            'order %s placed via cart checkout by user %s', order.id, user_id
        )

        return make_response(
            'checkout success',
            OrderDetailResponseSchema().dump(order),
            201,
        )
