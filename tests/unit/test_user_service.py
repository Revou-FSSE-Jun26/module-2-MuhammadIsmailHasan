"""
Unit tests for UserService.

UserRepository (and hash_password) are mocked so registration branching,
integrity-error mapping, and delete permission logic run without a database.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.services.user_service import (
    UserService,
    UserNotFoundError,
    UsernameAlreadyExistsError,
    EmailAlreadyExistsError,
    DeletePermissionError,
)


def make_user(id=1, username='u', email='u@test.com', is_active=True):
    return SimpleNamespace(id=id, username=username, email=email, is_active=is_active)


def integrity_error(message):
    # IntegrityError(statement, params, orig); str(e.orig) is inspected by service
    return IntegrityError('INSERT', {}, Exception(message))


@pytest.fixture
def repo():
    with patch('app.services.user_service.UserRepository') as mock_repo:
        yield mock_repo


@pytest.fixture(autouse=True)
def fake_hash():
    with patch('app.services.user_service.hash_password', return_value='hashed'):
        yield


class TestGetById:

    def test_success(self, repo):
        repo.get_by_id.return_value = make_user(id=3)
        assert UserService.get_by_id(3).id == 3

    def test_not_found(self, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(UserNotFoundError):
            UserService.get_by_id(3)


class TestRegister:

    def test_success(self, repo):
        repo.create.return_value = make_user(username='newuser')
        data = {'username': 'newuser', 'email': 'new@test.com',
                'password': 'secret', 'role': 'buyer'}

        result = UserService.register(data)
        assert result.username == 'newuser'
        # password must be hashed before hitting the repository
        repo.create.assert_called_once_with(data, 'hashed')

    def test_duplicate_username(self, repo):
        repo.create.side_effect = integrity_error('UNIQUE constraint failed: users.username')
        with patch('app.extensions.db'):
            with pytest.raises(UsernameAlreadyExistsError):
                UserService.register({
                    'username': 'dup', 'email': 'e@test.com',
                    'password': 'secret', 'role': 'buyer',
                })

    def test_duplicate_email(self, repo):
        repo.create.side_effect = integrity_error('UNIQUE constraint failed: users.email')
        with patch('app.extensions.db'):
            with pytest.raises(EmailAlreadyExistsError):
                UserService.register({
                    'username': 'u', 'email': 'dup@test.com',
                    'password': 'secret', 'role': 'buyer',
                })

    def test_other_integrity_error_maps_to_username_exists(self, repo):
        # a generic integrity error (no username/email token) falls back
        repo.create.side_effect = integrity_error('some other constraint')
        with patch('app.extensions.db'):
            with pytest.raises(UsernameAlreadyExistsError):
                UserService.register({
                    'username': 'u', 'email': 'e@test.com',
                    'password': 'secret', 'role': 'buyer',
                })


class TestDelete:

    def test_owner_can_delete_self(self, repo):
        user = make_user(id=5)
        repo.get_by_id.return_value = user

        UserService.delete(user_id=5, current_user_id=5, role='buyer')
        repo.soft_delete.assert_called_once_with(user)

    def test_admin_can_delete_other(self, repo):
        user = make_user(id=5)
        repo.get_by_id.return_value = user

        UserService.delete(user_id=5, current_user_id=1, role='admin')
        repo.soft_delete.assert_called_once_with(user)

    def test_non_owner_forbidden(self, repo):
        with pytest.raises(DeletePermissionError):
            UserService.delete(user_id=5, current_user_id=1, role='buyer')
        repo.soft_delete.assert_not_called()

    def test_permission_checked_before_existence(self, repo):
        # non-owner should be rejected without even looking up the user
        with pytest.raises(DeletePermissionError):
            UserService.delete(user_id=5, current_user_id=1, role='buyer')
        repo.get_by_id.assert_not_called()

    def test_not_found_for_authorized_user(self, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(UserNotFoundError):
            UserService.delete(user_id=5, current_user_id=5, role='buyer')
