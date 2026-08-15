from flask import Blueprint, jsonify, request
from models.user import User
from utils import db
from sqlalchemy.exc import IntegrityError
import bcrypt

user_bp = Blueprint('users', __name__, url_prefix='/users')

@user_bp.route('/register', methods=['POST'])
def register_user():
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
    
    try:
        new_user = User(
            username=data.get('username'),
            email=data.get('email'),
            password_hash = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt())
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
        
        return jsonify({
            'message': "username already exists",
            'status': False,
            'error': "this username is already registered"
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