from flask import Blueprint, jsonify, request
from models.user import User
from utils import db
from sqlalchemy.exc import IntegrityError
import bcrypt

user_bp = Blueprint('users', __name__, url_prefix='/users')

@user_bp.route('/register', methods=['POST'])
def register_user():
    """Register a new user.
    ---
    tags:
      - Users
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
            email:
              type: string
            password:
              type: string
            role:
              type: string
    responses:
      201:
        description: User created successfully
      400:
        description: Missing required fields
      409:
        description: Username or email already exists
    """
    
    data = request.get_json()
    
    if 'username' not in data:
        return jsonify({
                'message': "username is required",
                'status': False,
            }), 400 
    if 'email' not in data:
        return jsonify({
                'message': "email is required",
                'status': False,
            }), 400 
        
    if 'password' not in data:
        return jsonify({
                'message': "password is required",
                'status': False,
            }), 400 
    
    existing_user = User.query.filter_by(username=data.get('username')).first()
    if existing_user:
        return jsonify({
            'message': "username already exists",
            'status': False,
            'error': "this username is already registered"
        }), 409
    
    # Check if email already exists
    existing_email = User.query.filter_by(email=data.get('email')).first()
    if existing_email:
        return jsonify({
            'message': "email already exists",
            'status': False,
            'error': "this email is already registered"
        }), 409
    
    try:
        new_user = User(
            username=data.get('username'),
            email=data.get('email'),
            password_hash = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()),
            role=data.get('role', 'user')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'user created',
            'status': True,
            'data' : new_user.to_dict()
        }), 201
        
    except IntegrityError as error:
        db.session.rollback()
        
        error_message = str(error)
        if 'username' in error_message.lower():
            return jsonify({
                'message': "username already exists",
                'status': False,
                'error': "this username is already registered"
            }), 409
        elif 'email' in error_message.lower():
            return jsonify({
                'message': "email already exists",
                'status': False,
                'error': "this email is already registered"
            }), 409
        else:
            return jsonify({
                'message': "failed to create user",
                'status': False,
                'error': error_message
            }), 409
        
    except Exception as error:
        db.session.rollback()
        
        return jsonify({
            'message': "failed to create user",
            'status': False,
            'error': str(error)
        }), 400   

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID.
    ---
    tags:
      - Users
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: User found
      404:
        description: User not found
      500:
        description: Server error
    """
    try :
        user = User.query.get(user_id)
        if user :
            return jsonify({
                'message': 'success get user data',
                'status': True,
                'data' : user.to_dict()
            }), 200
        else :
            return jsonify({
                'message': "user data not found",
                'status': False,
            }), 404 
    except Exception as error :
        return jsonify({
            'message': "failed to get user data",
            'status': False,
            'error': str(error)
        }), 500 