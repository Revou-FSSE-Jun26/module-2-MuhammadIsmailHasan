from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.schemas.user_schema import (
    RegisterUserSchema,
    UserResponseSchema,
    UserPublicResponseSchema,
)
from app.services.user_service import (
    UserService,
    UserNotFoundError,
    UsernameAlreadyExistsError,
    EmailAlreadyExistsError,
    DeletePermissionError,
)
from app.auth import roles_required

users_blp = Blueprint(
    'users',
    __name__,
    url_prefix='/api/v1/users',
    description='User operations',
)


@users_blp.route('/')
class UserRegister(MethodView):

    @users_blp.arguments(RegisterUserSchema)
    def post(self, validated_data):
        try:
            user = UserService.register(validated_data)
        except UsernameAlreadyExistsError as e:
            abort(409, message=str(e))
        except EmailAlreadyExistsError as e:
            abort(409, message=str(e))

        return jsonify({
            'message': 'user created',
            'status': True,
            'data': UserResponseSchema().dump(user),
        }), 201


@users_blp.route('/me')
class UserMe(MethodView):

    @roles_required('seller', 'buyer', 'admin')
    def get(self):
        current_user_id = get_jwt_identity()

        try:
            user = UserService.get_by_id(int(current_user_id))
        except UserNotFoundError as e:
            abort(404, message=str(e))

        return jsonify({
            'message': 'get user data successful',
            'status': True,
            'data': UserResponseSchema().dump(user),
        }), 200


@users_blp.route('/<int:user_id>')
class UserDetail(MethodView):

    @roles_required('seller', 'buyer', 'admin')
    def get(self, user_id):
        try:
            user = UserService.get_by_id(user_id)
        except UserNotFoundError as e:
            abort(404, message=str(e))

        return jsonify({
            'message': 'success get user data',
            'status': True,
            'data': UserPublicResponseSchema().dump(user),
        }), 200

    @jwt_required()
    def delete(self, user_id):
        claims = get_jwt()
        current_user_id = int(get_jwt_identity())
        role = claims.get('role')

        try:
            UserService.delete(user_id, current_user_id, role)
        except DeletePermissionError as e:
            abort(403, message=str(e))
        except UserNotFoundError as e:
            abort(404, message=str(e))

        return jsonify({
            'message': 'success delete user',
            'status': True,
        }), 200
