from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.schemas.user_profile_schema import (
    UpdateProfileSchema,
    ProfileResponseSchema,
)
from app.services.user_profile_service import (
    UserProfileService,
    ProfileNotFoundError,
)
from app.auth import roles_required
from app.utils.auth_context import current_user_id
from app.utils.http import make_response

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
        try:
            profile = UserProfileService.get(current_user_id())
        except ProfileNotFoundError as e:
            abort(404, message=str(e))

        return make_response(
            'get profile success',
            ProfileResponseSchema().dump(profile),
        )

    @profile_blp.arguments(UpdateProfileSchema)
    @roles_required('buyer', 'seller', 'admin')
    def put(self, validated_data):
        profile = UserProfileService.upsert(current_user_id(), validated_data)

        return make_response(
            'profile saved',
            ProfileResponseSchema().dump(profile),
        )
