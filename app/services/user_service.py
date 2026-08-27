from sqlalchemy.exc import IntegrityError

from app.repositories.user_repository import UserRepository
from app.auth import hash_password


class UserNotFoundError(Exception):
    pass


class UsernameAlreadyExistsError(Exception):
    pass


class EmailAlreadyExistsError(Exception):
    pass


class DeletePermissionError(Exception):
    pass


class UserService:

    @staticmethod
    def get_by_id(user_id):
        user = UserRepository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("user data not found")
        return user

    @staticmethod
    def register(data):
        hashed = hash_password(data['password'])
        try:
            user = UserRepository.create(data, hashed)
        except IntegrityError as e:
            from app.extensions import db
            db.session.rollback()
            error_info = str(e.orig).lower() if e.orig else str(e).lower()
            if 'username' in error_info:
                raise UsernameAlreadyExistsError("username already exists")
            elif 'email' in error_info:
                raise EmailAlreadyExistsError("email already exists")
            raise UsernameAlreadyExistsError("failed to create user: data integrity violation")
        return user

    @staticmethod
    def delete(user_id, current_user_id, role):
        if role != 'admin' and current_user_id != user_id:
            raise DeletePermissionError("you don't have permission to delete this user")

        user = UserRepository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("user not found")

        UserRepository.soft_delete(user)
