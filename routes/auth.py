from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import datetime
from helper.utils import db
from models.users import User
from helper.auth import check_password

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login and receive JWT tokens.
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: john@example.com
            password:
              type: string
              example: password123
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            status:
              type: boolean
              example: true
            message:
              type: string
              example: login successful
            access_token:
              type: string
              example: eyJhbGciOiJIUzI1NiIs...
            refresh_token:
              type: string
              example: eyJhbGciOiJIUzI1NiIs...
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
      400:
        description: Missing email or password
        schema:
          type: object
          properties:
            message:
              type: string
              example: email and password are required
            status:
              type: boolean
              example: false
      401:
        description: Invalid credentials
        schema:
          type: object
          properties:
            message:
              type: string
              example: invalid email or password
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
              example: failed to login
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

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({
            'message': 'email and password are required',
            'status': False
        }), 400

    try:
        user = User.query.filter_by(is_active=True, email=email).first()
    except OperationalError as e:
        current_app.logger.error('operational error during login: %s', e)
        return jsonify({
            'message': 'failed to login: database connection issue',
            'status': False
        }), 503
    except SQLAlchemyError as e:
        current_app.logger.error('database error during login: %s', e)
        return jsonify({
            'message': 'failed to login',
            'status': False
        }), 500

    if user is None or not check_password(password, user.password_hash):
        return jsonify({
            'message': 'invalid email or password',
            'status': False
        }), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role}
    )

    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims={'role': user.role}
    )

    try:
        user.last_login = datetime.utcnow()
        db.session.commit()
    except OperationalError as e:
        db.session.rollback()
        current_app.logger.error('operational error updating last_login: %s', e)
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error('database error updating last_login: %s', e)

    return jsonify({
        'status': True,
        'message': 'login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'data': user.to_dict()
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Get a new access token using a refresh token.
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: "Bearer <refresh_token>"
    responses:
      200:
        description: New access token issued
        schema:
          type: object
          properties:
            status:
              type: boolean
              example: true
            message:
              type: string
              example: create new access token successful
            access_token:
              type: string
              example: eyJhbGciOiJIUzI1NiIs...
      401:
        description: Missing, invalid, or expired refresh token
        schema:
          type: object
          properties:
            message:
              type: string
              example: Token has expired
            status:
              type: boolean
              example: false
      404:
        description: User not found (deactivated)
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
              example: failed to refresh token
            status:
              type: boolean
              example: false
    """
    current_user_id = get_jwt_identity()

    try:
        user = User.query.filter_by(id=current_user_id, is_active=True).first()
    except OperationalError as e:
        current_app.logger.error('operational error during token refresh: %s', e)
        return jsonify({
            'message': 'failed to refresh token: database connection issue',
            'status': False
        }), 503
    except SQLAlchemyError as e:
        current_app.logger.error('database error during token refresh: %s', e)
        return jsonify({
            'message': 'failed to refresh token',
            'status': False
        }), 500

    if user is None:
        return jsonify({
            'message': 'user not found',
            'status': False
        }), 404

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role},
        fresh=False
    )

    return jsonify({
        'status': True,
        'message': 'create new access token successful',
        'access_token': access_token
    }), 200
