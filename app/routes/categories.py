from flask import Blueprint, jsonify, request
from app.models.categories import Category
from app.extensions import db
from app.validation import validation_category_data
from app.auth import roles_required

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
      - name: with_products
        in: query
        type: boolean
        required: false
      - name: sort_by
        in: query
        type: string
        required: false
        enum: [id, name, created_at]
      - name: order
        in: query
        type: string
        required: false
        enum: [asc, desc]
      - name: page
        in: query
        type: integer
        required: false
      - name: limit
        in: query
        type: integer
        required: false
    responses:
      200:
        description: Categories retrieved successfully
      500:
        description: Failed to get categories
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
    responses:
      201:
        description: Category created successfully
      400:
        description: Invalid input
      409:
        description: Category name already exists
      422:
        description: Validation error
      500:
        description: Server error
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

    existing = Category.query.filter_by(name=name, is_active=True).first()
    if existing:
        return jsonify({
            'message': 'category name already exists',
            'status': False
        }), 409

    category = Category(name=name)
    db.session.add(category)
    db.session.commit()

    return jsonify({
        'message': 'category created',
        'status': True,
        'data': category.to_dict()
    }), 201


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
    responses:
      200:
        description: Category found
      404:
        description: Category not found
      500:
        description: Server error
    """
    category = Category.query.filter_by(id=category_id, is_active=True).first()

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
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: Updated Electronics
    responses:
      200:
        description: Category updated
      400:
        description: Invalid input
      404:
        description: Category not found
      409:
        description: Category name already exists
      422:
        description: Validation error
      500:
        description: Server error
    """
    category = Category.query.filter_by(id=category_id, is_active=True).first()

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

    db.session.commit()

    return jsonify({
        'message': 'success update category',
        'status': True,
        'data': category.to_dict()
    }), 200


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
    responses:
      200:
        description: Category deleted
      404:
        description: Category not found
      500:
        description: Server error
    """
    category = Category.query.filter_by(id=category_id, is_active=True).first()

    if not category:
        return jsonify({
            'message': 'category not found',
            'status': False
        }), 404

    category.is_active = False
    db.session.commit()

    return jsonify({
        'message': 'success delete category',
        'status': True
    }), 200
