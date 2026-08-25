from flask import Blueprint, jsonify, request, current_app
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, DataError
from models.products import Product
from models.orders import Order, OrderItem
from helper.utils import db
from helper.validation import validation_products_data
from helper.auth import roles_required

products_bp = Blueprint('products', __name__, url_prefix='/products')


@products_bp.route('/', methods=['GET'])
@roles_required('buyer', 'seller', 'admin')
def get_products():
    """Get all products.
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: name
        in: query
        type: string
        required: false
        description: Filter by product name (partial match)
      - name: category_id
        in: query
        type: integer
        required: false
        description: Filter by category ID
      - name: min_price
        in: query
        type: number
        required: false
        description: Minimum price filter
      - name: max_price
        in: query
        type: number
        required: false
        description: Maximum price filter
      - name: sort_by
        in: query
        type: string
        required: false
        enum: [id, name, price, created_at]
        description: Sort field (default id)
      - name: order
        in: query
        type: string
        required: false
        enum: [asc, desc]
        description: Sort direction (default asc)
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
        description: Products retrieved successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: get all products success
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
                  name:
                    type: string
                    example: Laptop
                  price:
                    type: number
                    example: 999.99
                  stock:
                    type: integer
                    example: 50
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
                  example: 50
                total_pages:
                  type: integer
                  example: 5
      500:
        description: Failed to get products
        schema:
          type: object
          properties:
            message:
              type: string
              example: failed get all products
            status:
              type: boolean
              example: false
    """
    query = Product.query.filter_by(is_active=True)

    name = request.args.get('name')
    if name:
        query = query.filter(Product.name.ilike(f'%{name}%'))

    category_id = request.args.get('category_id', type=int)
    if category_id:
        query = query.filter_by(category_id=category_id)

    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')

    sort_columns = {
        'id': Product.id,
        'name': Product.name,
        'price': Product.price,
        'created_at': Product.created_at
    }
    sort_column = sort_columns.get(sort_by, Product.name)

    if order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    try:
        paginated = query.paginate(page=page, per_page=limit, error_out=False)

        return jsonify({
            'message': 'get all products success',
            'status': True,
            'data': [product.to_dict() for product in paginated.items],
            'pagination': {
                'page': paginated.page,
                'limit': paginated.per_page,
                'total_items': paginated.total,
                'total_pages': paginated.pages
            }
        }), 200

    except OperationalError as e:
        current_app.logger.error('operational error getting products: %s', e)
        return jsonify({
            'message': 'failed get all products: database connection issue',
            'status': False
        }), 503

    except SQLAlchemyError as e:
        current_app.logger.error('database error getting products: %s', e)
        return jsonify({
            'message': 'failed get all products',
            'status': False
        }), 500


@products_bp.route('/', methods=['POST'])
@roles_required('seller', 'admin')
def create_product():
    """Create a new product.
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - price
            - stock
          properties:
            name:
              type: string
              example: Laptop
              description: Product name (max 255 characters)
            description:
              type: string
              example: A powerful laptop
              description: Product description (max 1000 characters)
            price:
              type: number
              example: 999.99
              description: Product price (must be greater than 0, max 11 digits)
            stock:
              type: integer
              example: 50
              description: Product stock quantity
            category_id:
              type: integer
              example: 1
              description: Category ID (must reference an existing category)
    responses:
      201:
        description: Product created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: product created
            status:
              type: boolean
              example: true
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                name:
                  type: string
                  example: Laptop
                price:
                  type: number
                  example: 999.99
                stock:
                  type: integer
                  example: 50
      400:
        description: Invalid input or empty body
        schema:
          type: object
          properties:
            message:
              type: string
              example: name is required
            status:
              type: boolean
              example: false
      404:
        description: Category not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: category id not found
            status:
              type: boolean
              example: false
      422:
        description: Validation error (exceeds limits)
        schema:
          type: object
          properties:
            message:
              type: string
              example: name cannot exceed 255 characters
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
              example: failed to create product
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

    error_message, error_code = validation_products_data(data)
    if error_message is not None:
        return jsonify({
            'message': error_message,
            'status': False
        }), error_code

    try:
        product = Product(
            name=data.get('name').strip(),
            description=data.get('description'),
            price=data.get('price'),
            stock=data.get('stock', 0),
            category_id=data.get('category_id')
        )

        db.session.add(product)
        db.session.commit()

        return jsonify({
            'message': 'product created',
            'status': True,
            'data': product.to_dict()
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error('integrity error creating product: %s', e)
        return jsonify({
            'message': 'failed to create product: data integrity violation',
            'status': False
        }), 422

    except DataError as e:
        db.session.rollback()
        current_app.logger.error('data error creating product: %s', e)
        return jsonify({
            'message': 'failed to create product: invalid data format',
            'status': False
        }), 422

    except OperationalError as e:
        db.session.rollback()
        current_app.logger.error('operational error creating product: %s', e)
        return jsonify({
            'message': 'failed to create product: database connection issue',
            'status': False
        }), 503

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error('database error creating product: %s', e)
        return jsonify({
            'message': 'failed to create product',
            'status': False
        }), 500


@products_bp.route('/<int:product_id>', methods=['GET'])
@roles_required('seller', 'buyer', 'admin')
def get_product(product_id):
    """Get a product by ID.
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        description: The ID of the product to retrieve
    responses:
      200:
        description: Product found
        schema:
          type: object
          properties:
            message:
              type: string
              example: success get product
            status:
              type: boolean
              example: true
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                name:
                  type: string
                  example: Laptop
                price:
                  type: number
                  example: 999.99
                stock:
                  type: integer
                  example: 50
                description:
                  type: string
                  example: A powerful laptop
                created_at:
                  type: string
                  example: "2024-01-01T00:00:00"
                is_active:
                  type: boolean
                  example: true
                category:
                  type: object
                  properties:
                    id:
                      type: integer
                      example: 2
                    name:
                      type: string
                      example: Electronics
                    created_at:
                      type: string
                      example: "2024-01-01T00:00:00"
                    is_active:
                      type: boolean
                      example: true
      404:
        description: Product not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: product not found
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
              example: failed to get product
            status:
              type: boolean
              example: false
    """
    try:
        product = Product.query.filter_by(id=product_id, is_active=True).first()
    except OperationalError as e:
        current_app.logger.error('operational error getting product %s: %s', product_id, e)
        return jsonify({
            'message': 'failed to get product: database connection issue',
            'status': False
        }), 503
    except SQLAlchemyError as e:
        current_app.logger.error('database error getting product %s: %s', product_id, e)
        return jsonify({
            'message': 'failed to get product',
            'status': False
        }), 500

    if not product:
        return jsonify({
            'message': 'product not found',
            'status': False
        }), 404

    return jsonify({
        'message': 'success get product',
        'status': True,
        'data': product.to_dict_detail()
    }), 200


@products_bp.route('/<int:product_id>', methods=['PUT'])
@roles_required('seller', 'admin')
def update_product(product_id):
    """Update a product.
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        description: The ID of the product to update
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: Updated Laptop
              description: Product name (max 255 characters)
            description:
              type: string
              example: An updated powerful laptop
              description: Product description (max 1000 characters)
            price:
              type: number
              example: 1099.99
              description: Product price (must be greater than 0, max 11 digits)
            stock:
              type: integer
              example: 100
              description: Product stock quantity
            category_id:
              type: integer
              example: 2
              description: Category ID (must reference an existing category)
    responses:
      200:
        description: Product updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: success update product
            status:
              type: boolean
              example: true
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                name:
                  type: string
                  example: Updated Laptop
                price:
                  type: number
                  example: 1099.99
                stock:
                  type: integer
                  example: 100
      400:
        description: Invalid input or empty body
        schema:
          type: object
          properties:
            message:
              type: string
              example: body request must be valid JSON format or cannot be empty
            status:
              type: boolean
              example: false
      404:
        description: Product or category not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: Product not found
            status:
              type: boolean
              example: false
      422:
        description: Validation error (exceeds limits)
        schema:
          type: object
          properties:
            message:
              type: string
              example: price cannot exceed 11 digits number
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
              example: failed to update product
            status:
              type: boolean
              example: false
    """
    try:
        product = Product.query.filter_by(id=product_id, is_active=True).first()
    except OperationalError as e:
        current_app.logger.error('operational error updating product %s: %s', product_id, e)
        return jsonify({
            'message': 'failed to update product: database connection issue',
            'status': False
        }), 503
    except SQLAlchemyError as e:
        current_app.logger.error('database error updating product %s: %s', product_id, e)
        return jsonify({
            'message': 'failed to update product',
            'status': False
        }), 500

    if not product:
        return jsonify({
            'message': 'Product not found',
            'status': False
        }), 404

    data = request.get_json(silent=True, force=True)
    if not data:
        return jsonify({
            'message': 'body request must be valid JSON format or cannot be empty',
            'status': False
        }), 400

    error_message, error_code = validation_products_data(data, False)
    if error_message is not None:
        return jsonify({
            'message': error_message,
            'status': False
        }), error_code

    name = data.get('name')
    stock = data.get('stock')
    price = data.get('price')
    description = data.get('description')
    category_id = data.get('category_id')

    if name is not None:
        product.name = name.strip()
    if stock is not None:
        product.stock = stock
    if price is not None:
        product.price = price
    if description is not None:
        product.description = description
    if category_id is not None:
        product.category_id = category_id

    try:
        db.session.commit()

        return jsonify({
            'message': 'success update product',
            'status': True,
            'data': product.to_dict()
        }), 200

    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error('integrity error updating product %s: %s', product_id, e)
        return jsonify({
            'message': 'failed to update product: data integrity violation',
            'status': False
        }), 422

    except DataError as e:
        db.session.rollback()
        current_app.logger.error('data error updating product %s: %s', product_id, e)
        return jsonify({
            'message': 'failed to update product: invalid data format',
            'status': False
        }), 422

    except OperationalError as e:
        db.session.rollback()
        current_app.logger.error('operational error updating product %s: %s', product_id, e)
        return jsonify({
            'message': 'failed to update product: database connection issue',
            'status': False
        }), 503

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error('database error updating product %s: %s', product_id, e)
        return jsonify({
            'message': 'failed to update product',
            'status': False
        }), 500


@products_bp.route('/<int:product_id>', methods=['DELETE'])
@roles_required('seller', 'admin')
def delete_product(product_id):
    """Delete a product (soft-delete).
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        description: The ID of the product to delete
    responses:
      200:
        description: Product deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: success delete product
            status:
              type: boolean
              example: true
      404:
        description: Product not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: product not found
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
              example: failed to delete product
            status:
              type: boolean
              example: false
    """
    try:
        product = Product.query.filter_by(id=product_id, is_active=True).first()
    except OperationalError as e:
        current_app.logger.error('operational error deleting product %s: %s', product_id, e)
        return jsonify({
            'message': 'failed to delete product: database connection issue',
            'status': False
        }), 503
    except SQLAlchemyError as e:
        current_app.logger.error('database error deleting product %s: %s', product_id, e)
        return jsonify({
            'message': 'failed to delete product',
            'status': False
        }), 500

    if not product:
        return jsonify({
            'message': 'product not found',
            'status': False
        }), 404

    try:
        active_order_exists = db.session.query(OrderItem).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            OrderItem.product_id == product_id,
            Order.is_active == True,
            Order.status.in_(['waiting_for_payment', 'processing', 'shipped'])
        ).first()
    except OperationalError as e:
        current_app.logger.error('operational error deleting product %s: %s', product_id, e)
        return jsonify({
            'message': 'failed to delete product: database connection issue',
            'status': False
        }), 503
    except SQLAlchemyError as e:
        current_app.logger.error('database error deleting product %s: %s', product_id, e)
        return jsonify({
            'message': 'failed to delete product',
            'status': False
        }), 500

    if active_order_exists:
        return jsonify({
            'message': 'cannot delete product: product has active orders',
            'status': False
        }), 400
    
    try:
        product.is_active = False
        db.session.commit()

        return jsonify({
            'message': 'success delete product',
            'status': True
        }), 200

    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error('integrity error deleting product %s: %s', product_id, e)
        return jsonify({
            'message': 'failed to delete product: data integrity violation',
            'status': False
        }), 422

    except OperationalError as e:
        db.session.rollback()
        current_app.logger.error('operational error deleting product %s: %s', product_id, e)
        return jsonify({
            'message': 'failed to delete product: database connection issue',
            'status': False
        }), 503

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error('database error deleting product %s: %s', product_id, e)
        return jsonify({
            'message': 'failed to delete product',
            'status': False
        }), 500
