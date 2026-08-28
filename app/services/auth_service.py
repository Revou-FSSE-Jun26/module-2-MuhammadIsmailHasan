from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token

from app.repositories.user_repository import UserRepository
from app.auth import check_password


class InvalidCredentialsError(Exception):
    pass


class AuthService:

    @staticmethod
    def login(email, password):
        user = UserRepository.get_by_email(email)

        if user is None or not check_password(password, user.password_hash):
            current_app.logger.warning('failed login attempt for email=%s', email)
            raise InvalidCredentialsError("invalid email or password")

        current_app.logger.info('user %s logged in', user.id)

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'role': user.role},
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims={'role': user.role},
        )

        try:
            UserRepository.update_last_login(user)
        except Exception:
            from app.extensions import db
            db.session.rollback()
            current_app.logger.warning('failed to update last_login for user %s', user.id)

        return user, access_token, refresh_token

    @staticmethod
    def refresh(user_id):
        user = UserRepository.get_by_id(user_id)

        if user is None:
            from app.services.user_service import UserNotFoundError
            raise UserNotFoundError("user not found")

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'role': user.role},
            fresh=False,
        )

        return access_token
