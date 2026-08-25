from flask import Blueprint, jsonify, request, current_app
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, DataError
from models.categories import Category
from helper.utils import db
from helper.validation import validation_category_data
from helper.auth import roles_required

categories_bp = Blueprint('categories', __name__)


@categories_bp.route('/', methods=['GET'])
@roles_required('seller', 'buyer', 'admin')
def get_categories():
    """Get all categories.
    ---
    tags:
      - Categories
    security:
      - Bearer: []
    parameters:
      - name: name
        in: query
        type: string
        required: false
        description: Filter by category name (partial match)
      - name: with_products
        in: query
        type: boolean
        required: false
        description: Include products belonging to each category (default false)
      - name: sort_by
        in: query
        type: string
        required: false
        enum: [id, name, created_at]
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
        description: Categories retrieved successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: get all categories success
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
                    example: Electronics
                  created_at:
                    type: string
                    example: "2024-01-01T00:00:00"
                  is_active:
                    type: boolean
                    example: true
                  products:
                    type: array
                    description: Only included when with_products=true
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
                  example: 5
                total_pages:
                  type: integer
                  example: 1
      500:
        description: Failed to get categories
        schema:
          type: object
          properties:
            message:
              type: string
              example: failed get all categories
            status:
              type: boolean
              example: false
    """
    query = Category.query.filter_by(is_active=True)

    name = request.args.get('name')
    if name:
        query = query.filter(Category.name.ilike(f'%{name}%'))

    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')

    sort_columns = {
        'id': Category.id,
        'name': Category.name,
        'created_at': Category.created_at
    }
    sort_column = sort_columns.get(sort_by, Category.name)

    if order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    try:
        paginated = query.paginate(page=page, per_page=limit, error_out=False)

        with_products = request.args.get('with_products', 'false').lower() == 'true'
        if with_products:
            data = [category.to_dict_with_products() for category in paginated.items]
        else:
            data = [category.to_dict() for category in paginated.items]

        return jsonify({
            'message': 'get all categories success',
            'status': True,
            'data': data,
            'pagination': {
                'page': paginated.page,
                'limit': paginated.per_page,
                'total_items': paginated.total,
                'total_pages': paginated.pages
            }
        }), 200

    except OperationalError as e:
        current_app.logger.error('operational error getting categories: %s', e)
        return jsonify({
            'message': 'failed get all categories: database connection issue',
            'status': False
        }), 503

    except SQLAlchemyError as e:
        current_app.logger.error('database error getting categories: %s', e)
        return jsonify({
            'message': 'failed get all categories',
            'status': False
        }), 500


@categories_bp.route('/', methods=['POST'])
@roles_required('seller', 'admin')
def create_category():
    """Create a new category.
    ---
    tags:
      - Categories
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
          properties:
            name:
              type: string
              example: Electronics
              description: Category name (max 255 characters)
    responses:
      201:
        description: Category created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: category created
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
                  example: Electronics
                created_at:
                  type: string
                  example: "2024-01-01T00:00:00"
                is_active:
                  type: boolean
                  example: true
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
      409:
        description: Category name already exists
        schema:
          type: object
          properties:
            message:
              type: string
              example: category name already exists
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
              example: failed to create category
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

    error_message, error_code = validation_category_data(data)
    if error_message is not None:
        return jsonify({
            'message': error_message,
            'status': False
        }), error_code

    name = data.get('name').strip()

    try:
        existing = Category.query.filter_by(name=name, is_active=True).first()
    except OperationalError as e:
        current_app.logger.error('operational error creating category: %s', e)
        return jsonify({
            'message': 'failed to create category: database connection issue',
            'status': False
        }), 503
    except SQLAlchemyError as e:
        current_app.logger.error('database error creating category: %s', e)
        return jsonify({
            'message': 'failed to create category',
            'status': False
        }), 500

    if existing:
        return jsonify({
            'message': 'category name already exists',
            'status': False
        }), 409

    try:
        category = Category(name=name)

        db.session.add(category)
        db.session.commit()

        return jsonify({
            'message': 'category created',
            'status': True,
            'data': category.to_dict()
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error('integrity error creating category: %s', e)
        return jsonify({
            'message': 'failed to create category: data integrity violation',
            'status': False
        }), 422

    except DataError as e:
        db.session.rollback()
        current_app.logger.error('data error creating category: %s', e)
        return jsonify({
            'message': 'failed to create category: invalid data format',
            'status': False
        }), 422

    except OperationalError as e:
        db.session.rollback()
        current_app.logger.error('operational error creating category: %s', e)
        return jsonify({
            'message': 'failed to create category: database connection issue',
            'status': False
        }), 503

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error('database error creating category: %s', e)
        return jsonify({
            'message': 'failed to create category',
            'status': False
        }), 500


@categories_bp.route('/<int:category_id>', methods=['GET'])
@roles_required('seller', 'buyer', 'admin')
def get_category(category_id):
    """Get a category by ID.
    ---
    tags:
      - Categories
    security:
      - Bearer: []
    parameters:
      - name: category_id
        in: path
        type: integer
        required: true
        description: The ID of the category to retrieve
    responses:
      200:
        description: Category found
        schema:
          type: object
          properties:
            message:
              type: string
              example: success get category
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
                  example: Electronics
                created_at:
                  type: string
                  example: "2024-01-01T00:00:00"
                is_active:
                  type: boolean
                  example: true
                products:
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
      404:
        description: Category not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: category not found
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
              example: failed to get category
            status:
              type: boolean
              example: false
    """
    try:
        category = Category.query.filter_by(id=category_id, is_active=True).first()
    except OperationalError as e:
        current_app.logger.error('operational error getting category %s: %s', category_id, e)
        return jsonify({
            'message': 'failed to get category: database connection issue',
            'status': False
        }), 503
    except SQLAlchemyError as e:
        current_app.logger.error('database error getting category %s: %s', category_id, e)
        return jsonify({
            'message': 'failed to get category',
            'status': False
        }), 500

    if not category:
        return jsonify({
            'message': 'category not found',
            'status': False
        }), 404

    return jsonify({
        'message': 'success get category',
        'status': True,
        'data': category.to_dict_with_products()
    }), 200


@categories_bp.route('/<int:category_id>', methods=['PUT'])
@roles_required('seller', 'admin')
def update_category(category_id):
    """Update a category.
    ---
    tags:
      - Categories
    security:
      - Bearer: []
    parameters:
      - name: category_id
        in: path
        type: integer
        required: true
        description: The ID of the category to update
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: Updated Electronics
              description: Category name (max 255 characters)
    responses:
      200:
        description: Category updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: success update category
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
                  example: Updated Electronics
                created_at:
                  type: string
                  example: "2024-01-01T00:00:00"
                is_active:
                  type: boolean
                  example: true
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
        description: Category not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: category not found
            status:
              type: boolean
              example: false
      409:
        description: Category name already exists
        schema:
          type: object
          properties:
            message:
              type: string
              example: category name already exists
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
              example: failed to update category
            status:
              type: boolean
              example: false
    """
    try:
        category = Category.query.filter_by(id=category_id, is_active=True).first()
    except OperationalError as e:
        current_app.logger.error('operational error updating category %s: %s', category_id, e)
        return jsonify({
            'message': 'failed to update category: database connection issue',
            'status': False
        }), 503
    except SQLAlchemyError as e:
        current_app.logger.error('database error updating category %s: %s', category_id, e)
        return jsonify({
            'message': 'failed to update category',
            'status': False
        }), 500

    if not category:
        return jsonify({
            'message': 'category not found',
            'status': False
        }), 404

    data = request.get_json(silent=True, force=True)
    if not data:
        return jsonify({
            'message': 'body request must be valid JSON format or cannot be empty',
            'status': False
        }), 400

    error_message, error_code = validation_category_data(data, False)
    if error_message is not None:
        return jsonify({
            'message': error_message,
            'status': False
        }), error_code

    name = data.get('name')

    if name is not None:
        name = name.strip()
        duplicate = Category.query.filter(
            Category.name == name,
            Category.id != category_id,
            Category.is_active.is_(True)
        ).first()
        if duplicate:
            return jsonify({
                'message': 'category name already exists',
                'status': False
            }), 409
        category.name = name

    try:
        db.session.commit()

        return jsonify({
            'message': 'success update category',
            'status': True,
            'data': category.to_dict()
        }), 200

    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error('integrity error updating category %s: %s', category_id, e)
        return jsonify({
            'message': 'failed to update category: data integrity violation',
            'status': False
        }), 422

    except DataError as e:
        db.session.rollback()
        current_app.logger.error('data error updating category %s: %s', category_id, e)
        return jsonify({
            'message': 'failed to update category: invalid data format',
            'status': False
        }), 422

    except OperationalError as e:
        db.session.rollback()
        current_app.logger.error('operational error updating category %s: %s', category_id, e)
        return jsonify({
            'message': 'failed to update category: database connection issue',
            'status': False
        }), 503

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error('database error updating category %s: %s', category_id, e)
        return jsonify({
            'message': 'failed to update category',
            'status': False
        }), 500


@categories_bp.route('/<int:category_id>', methods=['DELETE'])
@roles_required('seller', 'admin')
def delete_category(category_id):
    """Delete a category (soft-delete).
    ---
    tags:
      - Categories
    security:
      - Bearer: []
    parameters:
      - name: category_id
        in: path
        type: integer
        required: true
        description: The ID of the category to delete
    responses:
      200:
        description: Category deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: success delete category
            status:
              type: boolean
              example: true
      404:
        description: Category not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: category not found
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
              example: failed to delete category
            status:
              type: boolean
              example: false
    """
    try:
        category = Category.query.filter_by(id=category_id, is_active=True).first()
    except OperationalError as e:
        current_app.logger.error('operational error deleting category %s: %s', category_id, e)
        return jsonify({
            'message': 'failed to delete category: database connection issue',
            'status': False
        }), 503
    except SQLAlchemyError as e:
        current_app.logger.error('database error deleting category %s: %s', category_id, e)
        return jsonify({
            'message': 'failed to delete category',
            'status': False
        }), 500

    if not category:
        return jsonify({
            'message': 'category not found',
            'status': False
        }), 404

    try:
        category.is_active = False
        db.session.commit()

        return jsonify({
            'message': 'success delete category',
            'status': True
        }), 200

    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error('integrity error deleting category %s: %s', category_id, e)
        return jsonify({
            'message': 'failed to delete category: data integrity violation',
            'status': False
        }), 422

    except OperationalError as e:
        db.session.rollback()
        current_app.logger.error('operational error deleting category %s: %s', category_id, e)
        return jsonify({
            'message': 'failed to delete category: database connection issue',
            'status': False
        }), 503

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error('database error deleting category %s: %s', category_id, e)
        return jsonify({
            'message': 'failed to delete category',
            'status': False
        }), 500
