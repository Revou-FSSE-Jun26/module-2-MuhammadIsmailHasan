from sqlalchemy.exc import IntegrityError

from app.repositories.user_repository import UserRepository
from app.auth import check_password, hash_password


class UserNotFoundError(Exception):
    pass


class UsernameAlreadyExistsError(Exception):
    pass


class EmailAlreadyExistsError(Exception):
    pass


class DeletePermissionError(Exception):
    pass


class WrongPasswordError(Exception):
    pass


class SamePasswordError(Exception):
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
    def change_email(user_id, email, current_password):
        user = UserService.get_by_id(user_id)
        if not check_password(current_password, user.password_hash):
            raise WrongPasswordError("current password is incorrect")
        if email == user.email:
            return user
        existing = UserRepository.get_by_email(email)
        if existing and existing.id != user.id:
            raise EmailAlreadyExistsError("email already exists")
        try:
            return UserRepository.update_email(user, email)
        except IntegrityError:
            from app.extensions import db
            db.session.rollback()
            raise EmailAlreadyExistsError("email already exists")

    @staticmethod
    def change_password(user_id, current_password, new_password):
        user = UserService.get_by_id(user_id)
        if not check_password(current_password, user.password_hash):
            raise WrongPasswordError("current password is incorrect")
        if current_password == new_password:
            raise SamePasswordError("new password must be different from the current password")
        UserRepository.update_password(user, hash_password(new_password))
        return user

    @staticmethod
    def delete(user_id, current_user_id, role):
        if role != 'admin' and current_user_id != user_id:
            raise DeletePermissionError("you don't have permission to delete this user")

        user = UserRepository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("user not found")

        UserRepository.soft_delete(user)
