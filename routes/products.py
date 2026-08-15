from flask import Blueprint, jsonify, request
from models.product import Product
from utils import db

products_bp = Blueprint('products', __name__, url_prefix='/products')

@products_bp.route('/', methods=['GET'])
def get_products():
    try:
        products = Product.query.all()
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
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({
            'message': "product name is required",
            'status': False,
        }), 400
    
    if data.get('price') is None:
        return jsonify({
            'message': "product price is required",
            'status': False,
        }), 400
    
    try:
        price = float(data.get('price'))
        if price <= 0:
            return jsonify({
                'message': "product price must be greater than 0",
                'status': False,
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            'message': "product price must be a valid number",
            'status': False,
        }), 400
    
    try:
        product = Product(
            name=data.get('name'),
            description=data.get('description'),
            price=price,
            stock=data.get('stock', 0)
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
    try :
        product = Product.query.get(product_id)
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
    data = request.get_json()
    
    try:
        product = Product.query.get(product_id)
        
        if not product :
            return jsonify({
                'message': "Product not found",
                'status': False,
            }), 404 

        # Validate price if provided
        if 'price' in data:
            try:
                price = float(data['price'])
                if price <= 0:
                    return jsonify({
                        'message': "product price must be greater than 0",
                        'status': False,
                    }), 400
                product.price = price
            except (ValueError, TypeError):
                return jsonify({
                    'message': "product price must be a valid number",
                    'status': False,
                }), 400
            
        if 'name' in data :
            product.name = data['name']
        if 'stock' in data :
            product.stock = data['stock']
        
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
    try:
        product = Product.query.get(product_id)
        
        if not product : 
            return jsonify({
                    'message': "product not found",
                    'status': False,
                }), 404 
        
        db.session.delete(product)
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