from flask import Blueprint, jsonify, request
from models.products import Product
from helper.utils import db
from helper.validation import validation_products_data

products_bp = Blueprint('products', __name__, url_prefix='/products')

@products_bp.route('/', methods=['GET'])
def get_products():
    """Get all products.
    ---
    tags:
      - Products
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
                  category_id:
                    type: integer
                    example: 2
                  name:
                    type: string
                    example: Laptop
                  description:
                    type: string
                    example: A powerful laptop
                  price:
                    type: number
                    example: 999.99
                  stock:
                    type: integer
                    example: 50
                  created_at:
                    type: string
                    example: "2024-01-01T00:00:00"
      404:
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
            error:
              type: string
    """
    try:
        products = Product.query.filter_by(is_active=True)
        return jsonify({
            'message': 'get all products success',
            'status': True,
            'data': 
                [product.to_dict() for product in products]
        }), 200
            
    except Exception as e:
        return jsonify({
            'message': 'failed get all products',
            'status': False,
            'error': str(e)
        }), 404
    

@products_bp.route('/', methods=['POST'])
def create_product():
    """Create a new product.
    ---
    tags:
      - Products
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
                category_id:
                  type: integer
                  example: 1
                name:
                  type: string
                  example: Laptop
                description:
                  type: string
                  example: A powerful laptop
                price:
                  type: number
                  example: 999.99
                stock:
                  type: integer
                  example: 50
                created_at:
                  type: string
                  example: "2024-01-01T00:00:00"
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
    """
    data = request.get_json(silent=True, force=True)
    if not data:
      return jsonify({
        "message" : "body request must be valid JSON format or cannot be empty",
        "status": False
      }), 400
      
    error_message, error_code = validation_products_data(data)
    if error_message is not None:
      return jsonify({
        "message": error_message,
        "status": False
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
          'data' : product.to_dict()
      }), 201
    
    except Exception as error:
        db.session.rollback()
        
        return jsonify({
            'message': "failed to create product",
            'status': False,
            'error': str(error)
        }), 400    

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a product by ID.
    ---
    tags:
      - Products
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
                category_id:
                  type: integer
                  example: 2
                name:
                  type: string
                  example: Laptop
                description:
                  type: string
                  example: A powerful laptop
                price:
                  type: number
                  example: 999.99
                stock:
                  type: integer
                  example: 50
                created_at:
                  type: string
                  example: "2024-01-01T00:00:00"
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
              example: failed to create product
            status:
              type: boolean
              example: false
            error:
              type: string
    """
    try :
        product = Product.query.filter_by(id=product_id,is_active=True).first()
        if product :
            return jsonify({
                'message': 'success get product',
                'status': True,
                'data' : product.to_dict()
            }), 200
        else :
            return jsonify({
                'message': "product not found",
                'status': False,
            }), 404 
    except Exception as error :
        return jsonify({
            'message': "failed to create product",
            'status': False,
            'error': str(error)
        }), 500    
    
@products_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product.
    ---
    tags:
      - Products
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
                category_id:
                  type: integer
                  example: 2
                name:
                  type: string
                  example: Updated Laptop
                description:
                  type: string
                  example: An updated powerful laptop
                price:
                  type: number
                  example: 1099.99
                stock:
                  type: integer
                  example: 100
                created_at:
                  type: string
                  example: "2024-01-01T00:00:00"
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
            error:
              type: string
    """
    product = Product.query.filter_by(id=product_id, is_active=True).first()
        
    if not product :
      return jsonify({
          'message': "Product not found",
          'status': False,
      }), 404 
          
    data = request.get_json(silent=True, force=True)
    if not data:
      return jsonify({
        "message" : "body request must be valid JSON format or cannot be empty",
        "status": False
      }), 400
      
    error_message, error_code = validation_products_data(data, False)
    if error_message is not None:
      return jsonify({
        "message": error_message,
        "status": False
      }), error_code
    
    name = data.get('name')
    stock = data.get('stock', 0)
    price = data.get('price')
    description = data.get('description')
    category_id = data.get('category_id')
    
    if name is not None : product.name = name.strip()
    if stock is not None : product.stock = stock
    if price is not None : product.price = price
    if description is not None : product.description = description
    if category_id is not None : product.category_id = category_id
    
    try:  
      db.session.commit()
      
      return jsonify({
              'message': 'success update product',
              'status': True,
              'data' : product.to_dict()
          }), 200
        
    except Exception as error :
        db.session.rollback()
        return jsonify({
            'message': "failed to update product",
            'status': False,
            'error': str(error)
        }), 500  

@products_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product (soft-delete).
    ---
    tags:
      - Products
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
            error:
              type: string
    """
    try:
        product = Product.query.filter_by(id=product_id, is_active=True).first()
        
        if not product : 
            return jsonify({
                    'message': "product not found",
                    'status': False,
                }), 404 
            
        product.is_active = False
        db.session.commit()
        
        return jsonify({
                'message': 'success delete product',
                'status': True,
            }), 200
    except Exception as error:
        return jsonify({
            'message': "failed to delete product",
            'status': False,
            'error': str(error)
        }), 500  