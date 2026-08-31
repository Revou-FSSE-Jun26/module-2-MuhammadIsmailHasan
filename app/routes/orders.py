from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import current_app

from app.schemas.order_schema import (
    CreateOrderSchema,
    UpdateOrderStatusSchema,
    ChangeOrderAddressSchema,
    OrderQuerySchema,
    OrderResponseSchema,
    OrderDetailResponseSchema,
)
from app.services.order_service import (
    OrderService,
    OrderNotFoundError,
    OrderPermissionError,
    ProductNotFoundError,
    InsufficientStockError,
    InvalidStatusTransitionError,
    OrderCannotBeDeletedError,
    ShippingAddressRequiredError,
    AddressNotFoundError,
    AddressChangeNotAllowedError,
    TrackingIdRequiredError,
)
from app.auth import roles_required
from app.utils.auth_context import current_user_id, current_role
from app.utils.http import make_response, paginate_meta

orders_blp = Blueprint(
    'orders',
    __name__,
    url_prefix='/api/v1/orders',
    description='Order operations',
)


@orders_blp.route('/')
class OrderList(MethodView):

    @orders_blp.arguments(OrderQuerySchema, location='query')
    @roles_required('buyer', 'seller', 'admin')
    def get(self, query_params):
        filters = {
            'status': query_params.get('status'),
            'include_deleted': query_params.get('include_deleted', False),
        }

        paginated = OrderService.get_all(
            user_id=current_user_id(),
            role=current_role(),
            filters=filters,
            sort_by=query_params['sort_by'],
            order=query_params['order'],
            page=query_params['page'],
            limit=query_params['limit'],
        )

        return make_response(
            'get all orders success',
            OrderResponseSchema(many=True).dump(paginated.items),
            pagination=paginate_meta(paginated),
        )

    @orders_blp.arguments(CreateOrderSchema)
    @roles_required('buyer')
    def post(self, validated_data):
        user_id = current_user_id()

        try:
            order = OrderService.create(user_id, validated_data)
        except AddressNotFoundError as e:
            abort(404, message=str(e))
        except ShippingAddressRequiredError as e:
            abort(422, message=str(e))
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except InsufficientStockError as e:
            abort(422, message=str(e))

        current_app.logger.info(
            'order %s placed by user %s', order.id, user_id
        )

        return make_response(
            'order created',
            OrderDetailResponseSchema().dump(order),
            201,
        )


@orders_blp.route('/<int:order_id>')
class OrderDetail(MethodView):

    @roles_required('buyer', 'seller', 'admin')
    def get(self, order_id):
        try:
            order = OrderService.get_by_id(
                order_id, user_id=current_user_id(), role=current_role()
            )
        except OrderNotFoundError as e:
            abort(404, message=str(e))
        except OrderPermissionError as e:
            abort(403, message=str(e))

        return make_response(
            'success get order',
            OrderDetailResponseSchema().dump(order),
        )

    @orders_blp.arguments(UpdateOrderStatusSchema)
    @roles_required('seller', 'admin')
    def put(self, validated_data, order_id):
        try:
            order = OrderService.update_status(
                order_id, validated_data,
                user_id=current_user_id(), role=current_role(),
            )
        except OrderNotFoundError as e:
            abort(404, message=str(e))
        except OrderPermissionError as e:
            abort(403, message=str(e))
        except TrackingIdRequiredError as e:
            abort(422, message=str(e))
        except InvalidStatusTransitionError as e:
            abort(400, message=str(e))

        return make_response(
            'success update order status',
            OrderResponseSchema().dump(order),
        )

    @roles_required('buyer', 'seller', 'admin')
    def delete(self, order_id):
        user_id = current_user_id()

        try:
            order, refund_note = OrderService.cancel(
                order_id, user_id=user_id, role=current_role()
            )
        except OrderNotFoundError as e:
            abort(404, message=str(e))
        except OrderPermissionError as e:
            abort(403, message=str(e))
        except OrderCannotBeDeletedError as e:
            abort(400, message=str(e))

        current_app.logger.info(
            'order %s cancelled by user %s', order.id, user_id
        )

        data = {'id': order.id, 'status': order.status}
        if refund_note:
            data['refund_note'] = refund_note

        return make_response('order cancelled successfully', data)


@orders_blp.route('/<int:order_id>/address')
class OrderAddress(MethodView):

    @orders_blp.arguments(ChangeOrderAddressSchema)
    @roles_required('buyer')
    def put(self, validated_data, order_id):
        try:
            order = OrderService.change_address(
                order_id, validated_data['address_id'], user_id=current_user_id()
            )
        except OrderNotFoundError as e:
            abort(404, message=str(e))
        except AddressNotFoundError as e:
            abort(404, message=str(e))
        except OrderPermissionError as e:
            abort(403, message=str(e))
        except AddressChangeNotAllowedError as e:
            abort(409, message=str(e))

        return make_response(
            'shipping address updated',
            OrderDetailResponseSchema().dump(order),
        )
