from flask import Blueprint, jsonify, request
from models.categories import Category
from helper.utils import db
from helper.validation import validation_categories_data

category_bp = Blueprint('categories', __name__, url_prefix='/categories')

@category_bp.route('/', methods=['GET'])
def get_categories():
    """Get all categories.
    ---
    tags:
      - Categories
    parameters:
      - name: name
        in: query
        type: string
        required: false
        description: Filter by category name (partial match)
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
      404:
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
            error:
              type: string
    """
    try:
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
        
        return jsonify({
            'message': 'get all categories success',
            'status': True,
            'data': [category.to_dict() for category in paginated.items],
            'pagination': {
                'page': paginated.page,
                'limit': paginated.per_page,
                'total_items': paginated.total,
                'total_pages': paginated.pages
            }
        }), 200
            
    except Exception as e:
        return jsonify({
            'message': 'failed get all categories',
            'status': False,
            'error': str(e)
        }), 404
    

@category_bp.route('/', methods=['POST'])
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
              example: body request must be valid JSON format or cannot be empty
            status:
              type: boolean
              example: false
      422:
        description: Validation error
        schema:
          type: object
          properties:
            message:
              type: string
              example: name cannot exceed 255 characters
            status:
              type: boolean
              example: false
    """
    data = request.get_json(silent=True, force=True)
    if not data:
      return jsonify({
        "message" : "body request must be valid JSON format or cannot be empty",
        "status": False
      }), 400
      
    error_message, error_code = validation_categories_data(data)
    if error_message is not None:
      return jsonify({
        "message": error_message,
        "status": False
      }), error_code
    
    
    try:
      category = Category(
          name=data.get('name').strip()
      )
      
      db.session.add(category)
      db.session.commit()
      
      return jsonify({
          'message': 'category created',
          'status': True,
          'data' : category.to_dict_detail()
      }), 201
    
    except Exception as error:
        db.session.rollback()
        
        return jsonify({
            'message': "failed to create category",
            'status': False,
            'error': str(error)
        }), 400    

@category_bp.route('/<int:category_id>', methods=['GET'])
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
            error:
              type: string
    """
    try :
        category = Category.query.filter_by(id=category_id,is_active=True).first()
        if category :
            return jsonify({
                'message': 'success get category',
                'status': True,
                'data' : category.to_dict_with_products()
            }), 200
        else :
            return jsonify({
                'message': "category not found",
                'status': False,
            }), 404 
    except Exception as error :
        return jsonify({
            'message': "failed to get category",
            'status': False,
            'error': str(error)
        }), 500    
    
@category_bp.route('/<int:category_id>', methods=['PUT'])
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
      422:
        description: Validation error
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
            error:
              type: string
    """
    category = Category.query.filter_by(id=category_id, is_active=True).first()
        
    if not category :
      return jsonify({
          'message': "category not found",
          'status': False,
      }), 404 
          
    data = request.get_json(silent=True, force=True)
    if not data:
      return jsonify({
        "message" : "body request must be valid JSON format or cannot be empty",
        "status": False
      }), 400
      
    error_message, error_code = validation_categories_data(data, False)
    if error_message is not None:
      return jsonify({
        "message": error_message,
        "status": False
      }), error_code
    
    name = data.get('name')
    
    if name is not None : category.name = name.strip()
    
    try:  
      db.session.commit()
      
      return jsonify({
              'message': 'success update category',
              'status': True,
              'data' : category.to_dict_detail()
          }), 200
        
    except Exception as error :
        db.session.rollback()
        return jsonify({
            'message': "failed to update category",
            'status': False,
            'error': str(error)
        }), 500  

@category_bp.route('/<int:category_id>', methods=['DELETE'])
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
            error:
              type: string
    """
    try:
        category = Category.query.filter_by(id=category_id, is_active=True).first()
        
        if not category : 
            return jsonify({
                    'message': "category not found",
                    'status': False,
                }), 404 
            
        category.is_active = False
        db.session.commit()
        
        return jsonify({
                'message': 'success delete category',
                'status': True,
            }), 200
    except Exception as error:
        return jsonify({
            'message': "failed to delete category",
            'status': False,
            'error': str(error)
        }), 500
