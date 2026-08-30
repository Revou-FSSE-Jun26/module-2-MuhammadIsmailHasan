from app.models.user_profiles import UserProfile
from app.extensions import db


class UserProfileRepository:

    @staticmethod
    def get_by_user_id(user_id):
        return UserProfile.query.filter_by(user_id=user_id, is_active=True).first()

    @staticmethod
    def create(user_id, data):
        profile = UserProfile(
            user_id=user_id,
            full_name=data.get('full_name'),
            phone=data.get('phone'),
            avatar_url=data.get('avatar_url'),
        )
        db.session.add(profile)
        db.session.commit()
        return profile

    @staticmethod
    def update(profile, data):
        for field in ('full_name', 'phone', 'avatar_url'):
            if field in data:
                setattr(profile, field, data[field])
        db.session.commit()
        return profile

    @staticmethod
    def soft_delete(profile):
        profile.is_active = False
        db.session.commit()
        return profile
