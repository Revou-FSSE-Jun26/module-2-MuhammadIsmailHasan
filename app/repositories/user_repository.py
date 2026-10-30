from app.models.users import User
from app.extensions import db
from app.utils.timezone import now_wib


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
        user.last_login = now_wib()
        db.session.commit()

    @staticmethod
    def update_email(user, email):
        user.email = email
        db.session.commit()
        return user

    @staticmethod
    def update_password(user, hashed_password):
        user.password_hash = hashed_password
        db.session.commit()
        return user

    @staticmethod
    def soft_delete(user):
        user.is_active = False
        db.session.commit()
