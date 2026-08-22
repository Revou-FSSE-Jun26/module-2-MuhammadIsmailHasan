from flask import Blueprint, jsonify, request, current_app
from models.categories import Category
from helper.utils import db
from helper.validation import validation_category_data

categories_bp = Blueprint('categories', __name__)


@categories_bp.route('/', methods=['GET'])
def get_categories():
    """Get all categories.
    ---
    tags:
      - Categories
    parameters:
      - name: with_products
        in: query
        type: boolean
        required: false
        description: Include the products belonging to each category
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
    try:
        with_products = request.args.get('with_products', 'false').lower() == 'true'
        categories = Category.query.filter_by(is_active=True).all()

        if with_products:
            data = [category.to_dict_with_products() for category in categories]
        else:
            data = [category.to_dict() for category in categories]

        return jsonify({
            'message': 'get all categories success',
            'status': True,
            'data': data
        }), 200

    except Exception:
        current_app.logger.exception('failed to get all categories')
        return jsonify({
            'message': 'failed get all categories',
            'status': False
        }), 500


@categories_bp.route('/', methods=['POST'])
def create_category():
    """Create a new category.
    ---
    tags:
      - Categories
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

    existing = Category.query.filter_by(name=name, is_active=True).first()
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

    except Exception:
        db.session.rollback()
        current_app.logger.exception('failed to create category')
        return jsonify({
            'message': 'failed to create category',
            'status': False
        }), 500


@categories_bp.route('/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """Get a category by ID.
    ---
    tags:
      - Categories
    parameters:
      - name: category_id
        in: path
        type: integer
        required: true
        description: The ID of the category to retrieve
      - name: with_products
        in: query
        type: boolean
        required: false
        description: Include the products belonging to this category
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

        if not category:
            return jsonify({
                'message': 'category not found',
                'status': False
            }), 404

        with_products = request.args.get('with_products', 'false').lower() == 'true'
        data = category.to_dict_with_products() if with_products else category.to_dict()

        return jsonify({
            'message': 'success get category',
            'status': True,
            'data': data
        }), 200

    except Exception:
        current_app.logger.exception('failed to get category %s', category_id)
        return jsonify({
            'message': 'failed to get category',
            'status': False
        }), 500


@categories_bp.route('/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Update a category.
    ---
    tags:
      - Categories
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

    try:
        db.session.commit()

        return jsonify({
            'message': 'success update category',
            'status': True,
            'data': category.to_dict()
        }), 200

    except Exception:
        db.session.rollback()
        current_app.logger.exception('failed to update category %s', category_id)
        return jsonify({
            'message': 'failed to update category',
            'status': False
        }), 500


@categories_bp.route('/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete a category (soft-delete).
    ---
    tags:
      - Categories
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

    except Exception:
        db.session.rollback()
        current_app.logger.exception('failed to delete category %s', category_id)
        return jsonify({
            'message': 'failed to delete category',
            'status': False
        }), 500
