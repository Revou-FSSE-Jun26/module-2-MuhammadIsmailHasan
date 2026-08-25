from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, get_jwt
from models.orders import Order, OrderItem
from models.products import Product
from helper.utils import db
from helper.validation import validation_order_data, validation_order_status, validation_delete_order
from helper.auth import roles_required
from decimal import Decimal

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')


@orders_bp.route('/', methods=['POST'])
@roles_required('buyer', 'admin')
def create_order():
    """Create a new order.
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - items
          properties:
            items:
              type: array
              items:
                type: object
                required:
                  - product_id
                  - quantity
                properties:
                  product_id:
                    type: integer
                    example: 1
                  quantity:
                    type: integer
                    example: 2
    responses:
      201:
        description: Order created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: order created
            status:
              type: boolean
              example: true
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                user_id:
                  type: integer
                  example: 1
                total_amount:
                  type: number
                  example: 1999.98
                status:
                  type: string
                  example: waiting_for_payment
                ordered_at:
                  type: string
                  example: "2024-01-01T00:00:00"
                is_active:
                  type: boolean
                  example: true
                items:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                        example: 1
                      product_id:
                        type: integer
                        example: 1
                      product_name:
                        type: string
                        example: Laptop
                      unit_price:
                        type: number
                        example: 999.99
                      quantity:
                        type: integer
                        example: 2
                      sub_total:
                        type: number
                        example: 1999.98
      400:
        description: Invalid input or empty body
        schema:
          type: object
          properties:
            message:
              type: string
              example: items is required
            status:
              type: boolean
              example: false
      404:
        description: Product not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: "product with id 99 not found"
            status:
              type: boolean
              example: false
      422:
        description: Insufficient stock
        schema:
          type: object
          properties:
            message:
              type: string
              example: "insufficient stock for product Laptop (available: 5, requested: 10)"
            status:
              type: boolean
              example: false
      500:
        description: Server error
        schema:
          type: object
          properties:
            message:
              type: string
              example: failed to create order
            status:
              type: boolean
              example: false
    """
    data = request.get_json(silent=True, force=True)
    if not data:
        return jsonify({
            'message': 'body request must be valid JSON format or cannot be empty',
            'status': False
        }), 400

    error_message, error_code = validation_order_data(data)
    if error_message is not None:
        return jsonify({
            'message': error_message,
            'status': False
        }), error_code

    current_user_id = int(get_jwt_identity())
    items_data = data.get('items')
    order_items = []
    total_amount = Decimal('0')

    for item in items_data:
        product = Product.query.filter_by(id=item['product_id'], is_active=True).first()
        if not product:
            return jsonify({
                'message': f"product with id {item['product_id']} not found",
                'status': False
            }), 404

        quantity = item['quantity']
        if product.stock < quantity:
            return jsonify({
                'message': f"insufficient stock for product {product.name} (available: {product.stock}, requested: {quantity})",
                'status': False
            }), 422

        unit_price = product.price
        sub_total = unit_price * quantity

        order_items.append({
            'product': product,
            'product_id': product.id,
            'unit_price': unit_price,
            'quantity': quantity,
            'sub_total': sub_total
        })

        total_amount += sub_total

    order = Order(
        user_id=current_user_id,
        total_amount=total_amount
    )
    db.session.add(order)
    db.session.flush()

    for item_data in order_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data['product_id'],
            unit_price=item_data['unit_price'],
            quantity=item_data['quantity'],
            sub_total=item_data['sub_total']
        )
        db.session.add(order_item)
        item_data['product'].stock -= item_data['quantity']

    db.session.commit()

    return jsonify({
        'message': 'order created',
        'status': True,
        'data': order.to_dict_detail()
    }), 201


@orders_bp.route('/', methods=['GET'])
@roles_required('buyer', 'seller', 'admin')
def get_orders():
    """Get all orders (own orders for buyer, all for admin).
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - name: status
        in: query
        type: string
        required: false
        enum: [waiting_for_payment, processing, shipped, delivered, cancelled]
        description: Filter by order status
      - name: include_deleted
        in: query
        type: string
        required: false
        enum: [true, false]
        description: Include deleted orders (default false)
      - name: sort_by
        in: query
        type: string
        required: false
        enum: [id, total_amount, ordered_at]
        description: Sort field (default id)
      - name: order
        in: query
        type: string
        required: false
        enum: [asc, desc]
        description: Sort direction (default desc)
      - name: page
        in: query
        type: integer
        required: false
        description: Page number (default 1)
      - name: limit
        in: query
        type: integer
        required: false
        description: Items per page (default 10)
    responses:
      200:
        description: Orders retrieved successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: get all orders success
            status:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  user_id:
                    type: integer
                    example: 1
                  total_amount:
                    type: number
                    example: 1999.98
                  status:
                    type: string
                    example: waiting_for_payment
                  ordered_at:
                    type: string
                    example: "2024-01-01T00:00:00"
            pagination:
              type: object
              properties:
                page:
                  type: integer
                  example: 1
                limit:
                  type: integer
                  example: 10
                total_items:
                  type: integer
                  example: 20
                total_pages:
                  type: integer
                  example: 2
      500:
        description: Server error
        schema:
          type: object
          properties:
            message:
              type: string
              example: failed to get orders
            status:
              type: boolean
              example: false
    """
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    role = claims.get('role')

    query = Order.query

    if role != 'admin':
        query = query.filter_by(user_id=current_user_id)

    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    if not include_deleted:
        query = query.filter_by(is_active=True)

    status_filter = request.args.get('status')
    if status_filter:
        query = query.filter_by(status=status_filter)

    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'desc')

    sort_columns = {
        'id': Order.id,
        'total_amount': Order.total_amount,
        'ordered_at': Order.ordered_at
    }
    sort_column = sort_columns.get(sort_by, Order.id)

    if order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    paginated = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'message': 'get all orders success',
        'status': True,
        'data': [o.to_dict() for o in paginated.items],
        'pagination': {
            'page': paginated.page,
            'limit': paginated.per_page,
            'total_items': paginated.total,
            'total_pages': paginated.pages
        }
    }), 200


@orders_bp.route('/<int:order_id>', methods=['GET'])
@roles_required('buyer', 'seller', 'admin')
def get_order(order_id):
    """Get order detail by ID (includes deleted/cancelled orders).
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - name: order_id
        in: path
        type: integer
        required: true
        description: The ID of the order to retrieve
    responses:
      200:
        description: Order found
        schema:
          type: object
          properties:
            message:
              type: string
              example: success get order
            status:
              type: boolean
              example: true
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                user_id:
                  type: integer
                  example: 1
                total_amount:
                  type: number
                  example: 1999.98
                status:
                  type: string
                  example: waiting_for_payment
                ordered_at:
                  type: string
                  example: "2024-01-01T00:00:00"
                is_active:
                  type: boolean
                  example: true
                items:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                        example: 1
                      product_id:
                        type: integer
                        example: 1
                      product_name:
                        type: string
                        example: Laptop
                      unit_price:
                        type: number
                        example: 999.99
                      quantity:
                        type: integer
                        example: 2
                      sub_total:
                        type: number
                        example: 1999.98
      403:
        description: Not allowed to view this order
        schema:
          type: object
          properties:
            message:
              type: string
              example: "you don't have permission to view this order"
            status:
              type: boolean
              example: false
      404:
        description: Order not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: order not found
            status:
              type: boolean
              example: false
      500:
        description: Server error
        schema:
          type: object
          properties:
            message:
              type: string
              example: failed to get order
            status:
              type: boolean
              example: false
    """
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    role = claims.get('role')

    order = Order.query.filter_by(id=order_id).first()

    if not order:
        return jsonify({
            'message': 'order not found',
            'status': False
        }), 404

    if role != 'admin' and order.user_id != current_user_id:
        return jsonify({
            'message': "you don't have permission to view this order",
            'status': False
        }), 403

    return jsonify({
        'message': 'success get order',
        'status': True,
        'data': order.to_dict_detail()
    }), 200


@orders_bp.route('/<int:order_id>', methods=['PUT'])
@roles_required('buyer', 'admin')
def update_order_status(order_id):
    """Update order status (must follow valid transitions: waiting_for_payment -> processing -> shipped -> delivered).
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - name: order_id
        in: path
        type: integer
        required: true
        description: The ID of the order to update
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - status
          properties:
            status:
              type: string
              enum: [waiting_for_payment, processing, shipped, delivered, cancelled]
              example: processing
    responses:
      200:
        description: Order status updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: success update order status
            status:
              type: boolean
              example: true
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                user_id:
                  type: integer
                  example: 1
                total_amount:
                  type: number
                  example: 1999.98
                status:
                  type: string
                  example: processing
                ordered_at:
                  type: string
                  example: "2024-01-01T00:00:00"
      400:
        description: Invalid input or empty body
        schema:
          type: object
          properties:
            message:
              type: string
              example: status is required
            status:
              type: boolean
              example: false
      403:
        description: Not allowed to update this order
        schema:
          type: object
          properties:
            message:
              type: string
              example: "you don't have permission to update this order"
            status:
              type: boolean
              example: false
      404:
        description: Order not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: order not found
            status:
              type: boolean
              example: false
      500:
        description: Server error
        schema:
          type: object
          properties:
            message:
              type: string
              example: failed to update order
            status:
              type: boolean
              example: false
    """
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    role = claims.get('role')

    order = Order.query.filter_by(id=order_id, is_active=True).first()

    if not order:
        return jsonify({
            'message': 'order not found',
            'status': False
        }), 404

    if role != 'admin' and order.user_id != current_user_id:
        return jsonify({
            'message': "you don't have permission to update this order",
            'status': False
        }), 403

    data = request.get_json(silent=True, force=True)
    if not data:
        return jsonify({
            'message': 'body request must be valid JSON format or cannot be empty',
            'status': False
        }), 400

    error_message, error_code = validation_order_status(data, current_status=order.status)
    if error_message is not None:
        return jsonify({
            'message': error_message,
            'status': False
        }), error_code

    order.status = data.get('status')
    db.session.commit()

    return jsonify({
        'message': 'success update order status',
        'status': True,
        'data': order.to_dict()
    }), 200


@orders_bp.route('/<int:order_id>', methods=['DELETE'])
@roles_required('buyer', 'admin')
def delete_order(order_id):
    """Cancel/delete an order. Blocked for shipped/delivered. Restores stock for waiting_for_payment/processing.
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - name: order_id
        in: path
        type: integer
        required: true
        description: The ID of the order to delete
    responses:
      200:
        description: Order cancelled/deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: order cancelled successfully
            status:
              type: boolean
              example: true
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                status:
                  type: string
                  example: cancelled
                refund_note:
                  type: string
                  example: payment refund will be processed
      400:
        description: Cannot delete order with current status
        schema:
          type: object
          properties:
            message:
              type: string
              example: "cannot delete order with status 'shipped'"
            status:
              type: boolean
              example: false
      403:
        description: Not allowed to delete this order
        schema:
          type: object
          properties:
            message:
              type: string
              example: "you don't have permission to delete this order"
            status:
              type: boolean
              example: false
      404:
        description: Order not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: order not found
            status:
              type: boolean
              example: false
      500:
        description: Server error
        schema:
          type: object
          properties:
            message:
              type: string
              example: failed to delete order
            status:
              type: boolean
              example: false
    """
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    role = claims.get('role')

    order = Order.query.filter_by(id=order_id, is_active=True).first()

    if not order:
        return jsonify({
            'message': 'order not found',
            'status': False
        }), 404

    if role != 'admin' and order.user_id != current_user_id:
        return jsonify({
            'message': "you don't have permission to delete this order",
            'status': False
        }), 403

    error_message, error_code = validation_delete_order(order.status)
    if error_message is not None:
        return jsonify({
            'message': error_message,
            'status': False
        }), error_code

    refund_note = None

    if order.status == 'cancelled':
        order.is_active = False
    elif order.status in ('waiting_for_payment', 'processing'):
        if order.status == 'processing':
            refund_note = 'payment refund will be processed'
        order.status = 'cancelled'
        order.is_active = False
        for item in order.items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock += item.quantity

    db.session.commit()

    response_data = {
        'message': 'order cancelled successfully',
        'status': True,
        'data': {
            'id': order.id,
            'status': order.status
        }
    }

    if refund_note:
        response_data['data']['refund_note'] = refund_note

    return jsonify(response_data), 200
