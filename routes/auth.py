from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity
from datetime import datetime
from helper.utils import db
from models.users import User
from helper.auth import check_password

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({
            "message" : "body request must be valid JSON format or cannot be empty",
            "status": False
        }), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({
            "message": "email and password are required",
            "status": False
        }), 400
    
    user = User.query.filter_by(is_active=True, email=email).first()
    if user is None or not check_password(password, user.password_hash):
        return jsonify({
            "message" : "invalid email or password",
            "status": False
        }), 401
        
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role}
    )
    
    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims={'role': user.role}
    )
    
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "status": True,
        "message": "login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "data": user.to_dict()
    }), 200
    
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    
    user = User.query.filter_by(id=current_user_id, is_active=True).first()
    if user is None:
        return jsonify({
            "message" : "user not found",
            "status": False
        }), 404
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role},
        fresh=False
    )
    
    return jsonify({
        "status": True,
        "message": "create new access token successful",
        "access_token": access_token,
    }), 200