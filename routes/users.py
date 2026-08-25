from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy.exc import IntegrityError
from models.users import User
from helper.utils import db
from helper.validation import validation_users_data
from helper.auth import hash_password, roles_required

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
            - role
          properties:
            username:
              type: string
              example: johndoe
            email:
              type: string
              example: john@example.com
            password:
              type: string
              example: password123
            role:
              type: string
              enum: [buyer, seller]
              example: buyer
              description: Only buyer or seller allowed. Admin cannot be self-registered.
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
        description: Missing required fields, invalid body, or invalid email format
        schema:
          type: object
          properties:
            message:
              type: string
              example: email is required
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
            'message': 'body request must be valid JSON format or cannot be empty',
            'status': False
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
            'data': new_user.to_dict()
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.warning('integrity error on user registration: %s', e)

        error_message = str(e).lower()
        if 'username' in error_message:
            return jsonify({
                'message': 'username already exists',
                'status': False
            }), 409
        elif 'email' in error_message:
            return jsonify({
                'message': 'email already exists',
                'status': False
            }), 409
        else:
            return jsonify({
                'message': 'failed to create user: data integrity violation',
                'status': False
            }), 409


@users_bp.route('/me', methods=['GET'])
@roles_required('seller', 'buyer', 'admin')
def get_user_account():
    """Get the authenticated user's own account.
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: User data retrieved successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: get user data successful
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
                  example: "2024-01-15T10:30:00"
                created_at:
                  type: string
                  example: "2024-01-01T00:00:00"
      401:
        description: Missing or invalid token
        schema:
          type: object
          properties:
            message:
              type: string
              example: Missing Authorization Header
            status:
              type: boolean
              example: false
      404:
        description: User not found (deactivated account)
        schema:
          type: object
          properties:
            message:
              type: string
              example: user data not found
            status:
              type: boolean
              example: false
    """
    current_user_id = get_jwt_identity()

    user = User.query.filter_by(id=current_user_id, is_active=True).first()

    if user is None:
        return jsonify({
            'message': 'user data not found',
            'status': False
        }), 404

    return jsonify({
        'message': 'get user data successful',
        'status': True,
        'data': user.to_dict()
    }), 200


@users_bp.route('/<int:user_id>', methods=['GET'])
@roles_required('seller', 'buyer', 'admin')
def get_user(user_id):
    """Get user public info by ID.
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: The ID of the user to retrieve
    responses:
      200:
        description: User found
        schema:
          type: object
          properties:
            message:
              type: string
              example: success get user data
            status:
              type: boolean
              example: true
            data:
              type: object
              properties:
                username:
                  type: string
                  example: johndoe
                email:
                  type: string
                  example: john@example.com
      401:
        description: Missing or invalid token
        schema:
          type: object
          properties:
            message:
              type: string
              example: Missing Authorization Header
            status:
              type: boolean
              example: false
      404:
        description: User not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: user data not found
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
              example: failed to get user data
            status:
              type: boolean
              example: false
    """
    user = User.query.filter_by(id=user_id, is_active=True).first()

    if not user:
        return jsonify({
            'message': 'user data not found',
            'status': False
        }), 404

    return jsonify({
        'message': 'success get user data',
        'status': True,
        'data': user.to_dict_public()
    }), 200


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete (soft-delete) a user. Only the user themselves or an admin can delete.
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: The ID of the user to delete
    responses:
      200:
        description: User deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: success delete user
            status:
              type: boolean
              example: true
      401:
        description: Missing or invalid token
        schema:
          type: object
          properties:
            message:
              type: string
              example: Missing Authorization Header
            status:
              type: boolean
              example: false
      403:
        description: Not allowed to delete this user
        schema:
          type: object
          properties:
            message:
              type: string
              example: "you don't have permission to delete this user"
            status:
              type: boolean
              example: false
      404:
        description: User not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: user not found
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
              example: failed to delete user
            status:
              type: boolean
              example: false
    """
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    role = claims.get('role')

    if role != 'admin' and current_user_id != user_id:
        return jsonify({
            'message': "you don't have permission to delete this user",
            'status': False
        }), 403

    user = User.query.filter_by(id=user_id, is_active=True).first()

    if not user:
        return jsonify({
            'message': 'user not found',
            'status': False
        }), 404

    user.is_active = False
    db.session.commit()

    return jsonify({
        'message': 'success delete user',
        'status': True
    }), 200
