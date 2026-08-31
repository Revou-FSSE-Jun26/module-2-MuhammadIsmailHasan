from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.schemas.user_schema import LoginSchema, UserResponseSchema
from app.services.auth_service import AuthService, InvalidCredentialsError
from app.services.user_service import UserNotFoundError
from app.utils.http import make_response

auth_blp = Blueprint(
    'auth',
    __name__,
    url_prefix='/api/v1/auth',
    description='Authentication operations',
)


@auth_blp.route('/login')
class AuthLogin(MethodView):

    @auth_blp.arguments(LoginSchema)
    def post(self, validated_data):
        try:
            user, access_token, refresh_token = AuthService.login(
                validated_data['email'],
                validated_data['password'],
            )
        except InvalidCredentialsError as e:
            abort(401, message=str(e))

        return make_response(
            'login successful',
            UserResponseSchema().dump(user),
            access_token=access_token,
            refresh_token=refresh_token,
        )


@auth_blp.route('/refresh')
class AuthRefresh(MethodView):

    @jwt_required(refresh=True)
    def post(self):
        current_user_id = get_jwt_identity()

        try:
            access_token = AuthService.refresh(int(current_user_id))
        except UserNotFoundError as e:
            abort(404, message=str(e))

        return make_response(
            'create new access token successful',
            access_token=access_token,
        )
