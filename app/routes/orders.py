from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import jsonify, current_app
from flask_jwt_extended import get_jwt_identity, get_jwt

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
)
from app.auth import roles_required

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
        claims = get_jwt()
        current_user_id = int(get_jwt_identity())
        role = claims.get('role')

        filters = {
            'status': query_params.get('status'),
            'include_deleted': query_params.get('include_deleted', False),
        }

        paginated = OrderService.get_all(
            user_id=current_user_id,
            role=role,
            filters=filters,
            sort_by=query_params['sort_by'],
            order=query_params['order'],
            page=query_params['page'],
            limit=query_params['limit'],
        )

        return jsonify({
            'message': 'get all orders success',
            'status': True,
            'data': OrderResponseSchema(many=True).dump(paginated.items),
            'pagination': {
                'page': paginated.page,
                'limit': paginated.per_page,
                'total_items': paginated.total,
                'total_pages': paginated.pages,
            },
        }), 200

    @orders_blp.arguments(CreateOrderSchema)
    @roles_required('buyer')
    def post(self, validated_data):
        current_user_id = int(get_jwt_identity())

        try:
            order = OrderService.create(current_user_id, validated_data)
        except AddressNotFoundError as e:
            abort(404, message=str(e))
        except ShippingAddressRequiredError as e:
            abort(422, message=str(e))
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except InsufficientStockError as e:
            abort(422, message=str(e))

        current_app.logger.info(
            'order %s placed by user %s', order.id, current_user_id
        )

        return jsonify({
            'message': 'order created',
            'status': True,
            'data': OrderDetailResponseSchema().dump(order),
        }), 201


@orders_blp.route('/<int:order_id>')
class OrderDetail(MethodView):

    @roles_required('buyer', 'seller', 'admin')
    def get(self, order_id):
        claims = get_jwt()
        current_user_id = int(get_jwt_identity())
        role = claims.get('role')

        try:
            order = OrderService.get_by_id(order_id, user_id=current_user_id, role=role)
        except OrderNotFoundError as e:
            abort(404, message=str(e))
        except OrderPermissionError as e:
            abort(403, message=str(e))

        return jsonify({
            'message': 'success get order',
            'status': True,
            'data': OrderDetailResponseSchema().dump(order),
        }), 200

    @orders_blp.arguments(UpdateOrderStatusSchema)
    @roles_required('seller', 'admin')
    def put(self, validated_data, order_id):
        claims = get_jwt()
        current_user_id = int(get_jwt_identity())
        role = claims.get('role')

        try:
            order = OrderService.update_status(
                order_id, validated_data, user_id=current_user_id, role=role
            )
        except OrderNotFoundError as e:
            abort(404, message=str(e))
        except OrderPermissionError as e:
            abort(403, message=str(e))
        except InvalidStatusTransitionError as e:
            abort(400, message=str(e))

        return jsonify({
            'message': 'success update order status',
            'status': True,
            'data': OrderResponseSchema().dump(order),
        }), 200

    @roles_required('buyer', 'seller', 'admin')
    def delete(self, order_id):
        claims = get_jwt()
        current_user_id = int(get_jwt_identity())
        role = claims.get('role')

        try:
            order, refund_note = OrderService.cancel(
                order_id, user_id=current_user_id, role=role
            )
        except OrderNotFoundError as e:
            abort(404, message=str(e))
        except OrderPermissionError as e:
            abort(403, message=str(e))
        except OrderCannotBeDeletedError as e:
            abort(400, message=str(e))

        current_app.logger.info(
            'order %s cancelled by user %s', order.id, current_user_id
        )

        response_data = {
            'message': 'order cancelled successfully',
            'status': True,
            'data': {
                'id': order.id,
                'status': order.status,
            },
        }

        if refund_note:
            response_data['data']['refund_note'] = refund_note

        return jsonify(response_data), 200


@orders_blp.route('/<int:order_id>/address')
class OrderAddress(MethodView):

    @orders_blp.arguments(ChangeOrderAddressSchema)
    @roles_required('buyer')
    def put(self, validated_data, order_id):
        current_user_id = int(get_jwt_identity())

        try:
            order = OrderService.change_address(
                order_id, validated_data['address_id'], user_id=current_user_id
            )
        except OrderNotFoundError as e:
            abort(404, message=str(e))
        except AddressNotFoundError as e:
            abort(404, message=str(e))
        except OrderPermissionError as e:
            abort(403, message=str(e))
        except AddressChangeNotAllowedError as e:
            abort(409, message=str(e))

        return jsonify({
            'message': 'shipping address updated',
            'status': True,
            'data': OrderDetailResponseSchema().dump(order),
        }), 200
