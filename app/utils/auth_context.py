from flask_jwt_extended import get_jwt, get_jwt_identity


def current_user_id():
    return int(get_jwt_identity())


def current_role():
    return get_jwt().get('role')
