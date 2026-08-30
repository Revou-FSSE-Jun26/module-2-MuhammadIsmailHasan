from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from app.schemas.user_profile_schema import (
    UpdateProfileSchema,
    ProfileResponseSchema,
)
from app.services.user_profile_service import (
    UserProfileService,
    ProfileNotFoundError,
)
from app.auth import roles_required

profile_blp = Blueprint(
    'profile',
    __name__,
    url_prefix='/api/v1/profile',
    description='Current user profile operations',
)


@profile_blp.route('')
class ProfileResource(MethodView):

    @roles_required('buyer', 'seller', 'admin')
    def get(self):
        current_user_id = int(get_jwt_identity())

        try:
            profile = UserProfileService.get(current_user_id)
        except ProfileNotFoundError as e:
            abort(404, message=str(e))

        return jsonify({
            'message': 'get profile success',
            'status': True,
            'data': ProfileResponseSchema().dump(profile),
        }), 200

    @profile_blp.arguments(UpdateProfileSchema)
    @roles_required('buyer', 'seller', 'admin')
    def put(self, validated_data):
        current_user_id = int(get_jwt_identity())
        profile = UserProfileService.upsert(current_user_id, validated_data)

        return jsonify({
            'message': 'profile saved',
            'status': True,
            'data': ProfileResponseSchema().dump(profile),
        }), 200
