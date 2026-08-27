from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy.exc import IntegrityError
from app.models.users import User
from app.extensions import db
from app.validation import validation_users_data
from app.auth import hash_password, roles_required

users_bp = Blueprint('users', __name__)


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
    responses:
      201:
        description: User created successfully
      400:
        description: Missing required fields or invalid body
      409:
        description: Username or email already exists
      500:
        description: Server error
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

        error_info = str(e.orig).lower() if e.orig else str(e).lower()
        if 'username' in error_info:
            return jsonify({
                'message': 'username already exists',
                'status': False
            }), 409
        elif 'email' in error_info:
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
      401:
        description: Missing or invalid token
      404:
        description: User not found
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
    responses:
      200:
        description: User found
      404:
        description: User not found
      500:
        description: Server error
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
    """Delete (soft-delete) a user.
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
    responses:
      200:
        description: User deleted successfully
      403:
        description: Not allowed to delete this user
      404:
        description: User not found
      500:
        description: Server error
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
