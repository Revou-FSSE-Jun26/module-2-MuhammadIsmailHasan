from app.models.users import User
from app.extensions import db
from app.utils.timezone import utcnow


class UserRepository:

    @staticmethod
    def get_by_id(user_id):
        return User.query.filter_by(id=user_id, is_active=True).first()

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email, is_active=True).first()

    @staticmethod
    def create(data, hashed_password):
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=hashed_password,
            role=data.get('role', 'buyer'),
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update_last_login(user):
        user.last_login = utcnow()
        db.session.commit()

    @staticmethod
    def soft_delete(user):
        user.is_active = False
        db.session.commit()
