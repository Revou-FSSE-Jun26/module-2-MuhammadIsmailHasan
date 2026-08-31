from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required

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
from app.utils.auth_context import current_user_id, current_role
from app.utils.http import make_response

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

        return make_response(
            'user created',
            UserResponseSchema().dump(user),
            201,
        )


@users_blp.route('/me')
class UserMe(MethodView):

    @roles_required('seller', 'buyer', 'admin')
    def get(self):
        try:
            user = UserService.get_by_id(current_user_id())
        except UserNotFoundError as e:
            abort(404, message=str(e))

        return make_response(
            'get user data successful',
            UserResponseSchema().dump(user),
        )


@users_blp.route('/<int:user_id>')
class UserDetail(MethodView):

    @roles_required('seller', 'buyer', 'admin')
    def get(self, user_id):
        try:
            user = UserService.get_by_id(user_id)
        except UserNotFoundError as e:
            abort(404, message=str(e))

        return make_response(
            'success get user data',
            UserPublicResponseSchema().dump(user),
        )

    @jwt_required()
    def delete(self, user_id):
        try:
            UserService.delete(user_id, current_user_id(), current_role())
        except DeletePermissionError as e:
            abort(403, message=str(e))
        except UserNotFoundError as e:
            abort(404, message=str(e))

        return make_response('success delete user')
