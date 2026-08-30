from app.repositories.user_profile_repository import UserProfileRepository


class ProfileNotFoundError(Exception):
    pass


class UserProfileService:

    @staticmethod
    def get(user_id):
        profile = UserProfileRepository.get_by_user_id(user_id)
        if not profile:
            raise ProfileNotFoundError("profile not found")
        return profile

    @staticmethod
    def upsert(user_id, data):
        profile = UserProfileRepository.get_by_user_id(user_id)
        if profile:
            return UserProfileRepository.update(profile, data)
        return UserProfileRepository.create(user_id, data)
