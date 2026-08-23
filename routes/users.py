from flask import Blueprint, jsonify, request, current_app
from models.users import User
from helper.utils import db
from sqlalchemy.exc import IntegrityError
from helper.validation import validation_users_data
from helper.auth import hash_password
import bcrypt

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/', methods=['POST'])
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
    responses:
      201:
        description: User created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: user created
            status:
              type: boolean
              example: true
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                username:
                  type: string
                  example: johndoe
                email:
                  type: string
                  example: john@example.com
                role:
                  type: string
                  example: buyer
                last_login:
                  type: string
                  example: null
                created_at:
                  type: string
                  example: "2024-01-01T00:00:00"
      400:
        description: Missing required fields or invalid body
        schema:
          type: object
          properties:
            message:
              type: string
              example: username is required
            status:
              type: boolean
              example: false
      409:
        description: Username or email already exists
        schema:
          type: object
          properties:
            message:
              type: string
              example: username already exists
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
              example: failed to create user
            status:
              type: boolean
              example: false
    """

    data = request.get_json(silent=True, force=True)
    if not data:
        return jsonify({
            "message": "body request must be valid JSON format or cannot be empty",
            "status": False
        }), 400

    error_message, error_code = validation_users_data(data, True)
    if error_message is not None:
        return jsonify({
            'message': error_message,
            'status': False
        }), error_code 
    
    try:
        new_user = User(
            username=data.get('username'),
            email=data.get('email'),
            password_hash=hash_password(data['password']),
            role=data.get('role', 'buyer')
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
        current_app.logger.warning('integrity error on user registration: %s', error)

        error_message = str(error).lower()
        if 'username' in error_message:
            return jsonify({
                'message': "username already exists",
                'status': False
            }), 409
        elif 'email' in error_message:
            return jsonify({
                'message': "email already exists",
                'status': False
            }), 409
        else:
            return jsonify({
                'message': "failed to create user",
                'status': False
            }), 409

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('failed to create user')

        return jsonify({
            'message': "failed to create user",
            'status': False
        }), 500   

@users_bp.route('/<int:user_id>', methods=['GET'])
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
        user = User.query.filter_by(id=user_id, is_active=True).first()
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
    except Exception :
        current_app.logger.exception('failed to get user %s', user_id)
        return jsonify({
            'message': "failed to get user data",
            'status': False
        }), 500 
        
@users_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete (soft-delete) a user by ID.
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
        description: User deleted successfully
      404:
        description: User not found
      500:
        description: Server error
    """
    try:
        user = User.query.filter_by(id=user_id, is_active=True).first()
        
        if not user : 
            return jsonify({
                    'message': "user not found",
                    'status': False,
                }), 404 
            
        user.is_active = False
        db.session.commit()
        
        return jsonify({
                'message': 'success delete user',
                'status': True,
            }), 200
    except Exception:
        db.session.rollback()
        current_app.logger.exception('failed to delete user %s', user_id)
        return jsonify({
            'message': "failed to delete user",
            'status': False
        }), 500