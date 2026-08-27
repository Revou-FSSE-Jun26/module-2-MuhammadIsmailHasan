from functools import wraps

import bcrypt
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def hash_password(plain_password):
    return bcrypt.hashpw(str(plain_password).encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def check_password(plain_password, hashed_password):
    return bcrypt.checkpw(str(plain_password).encode('utf-8'), hashed_password.encode('utf-8'))


def roles_required(*allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role', 'user')

            if user_role not in allowed_roles:
                return jsonify({
                    "status": False,
                    "message": f"Access denied. Required role(s): {', '.join(allowed_roles)}"
                }), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper
