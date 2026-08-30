from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services.user_address_service import (
    UserAddressService,
    AddressNotFoundError,
    DefaultAddressError,
)


def make_address(id=1, user_id=1, is_default=False):
    return SimpleNamespace(id=id, user_id=user_id, is_default=is_default)


@pytest.fixture
def repo():
    with patch('app.services.user_address_service.UserAddressRepository') as mock_repo:
        yield mock_repo


class TestCreateAddress:

    def test_first_address_becomes_default(self, repo):
        repo.count.return_value = 0
        repo.create.return_value = make_address(is_default=True)

        UserAddressService.create_address(1, {'city': 'X'}, make_default=False)

        # first address forced default; no need to clear since none existed
        repo.clear_default.assert_not_called()
        repo.create.assert_called_once_with(1, {'city': 'X'}, is_default=True)

    def test_second_address_not_default_by_default(self, repo):
        repo.count.return_value = 1

        UserAddressService.create_address(1, {'city': 'X'}, make_default=False)

        repo.clear_default.assert_not_called()
        repo.create.assert_called_once_with(1, {'city': 'X'}, is_default=False)

    def test_explicit_default_clears_previous(self, repo):
        repo.count.return_value = 2

        UserAddressService.create_address(1, {'city': 'X'}, make_default=True)

        repo.clear_default.assert_called_once_with(1)
        repo.create.assert_called_once_with(1, {'city': 'X'}, is_default=True)


class TestSetDefault:

    def test_set_default_clears_others(self, repo):
        target = make_address(id=5, is_default=False)
        repo.get.return_value = target

        UserAddressService.set_default(1, 5)

        repo.clear_default.assert_called_once_with(1)
        repo.set_default.assert_called_once_with(target)

    def test_set_default_noop_when_already_default(self, repo):
        target = make_address(id=5, is_default=True)
        repo.get.return_value = target

        result = UserAddressService.set_default(1, 5)

        repo.clear_default.assert_not_called()
        repo.set_default.assert_not_called()
        assert result is target

    def test_set_default_missing_raises(self, repo):
        repo.get.return_value = None

        with pytest.raises(AddressNotFoundError):
            UserAddressService.set_default(1, 99)


class TestDeleteAddress:

    def test_delete_non_default(self, repo):
        addr = make_address(id=2, is_default=False)
        repo.get.return_value = addr
        repo.count.return_value = 3

        UserAddressService.delete_address(1, 2)

        repo.soft_delete.assert_called_once_with(addr)

    def test_delete_default_blocked_when_others_exist(self, repo):
        addr = make_address(id=1, is_default=True)
        repo.get.return_value = addr
        repo.count.return_value = 2

        with pytest.raises(DefaultAddressError):
            UserAddressService.delete_address(1, 1)

        repo.soft_delete.assert_not_called()

    def test_delete_default_allowed_when_last(self, repo):
        addr = make_address(id=1, is_default=True)
        repo.get.return_value = addr
        repo.count.return_value = 1

        UserAddressService.delete_address(1, 1)

        repo.soft_delete.assert_called_once_with(addr)

    def test_delete_missing_raises(self, repo):
        repo.get.return_value = None

        with pytest.raises(AddressNotFoundError):
            UserAddressService.delete_address(1, 99)


class TestUpdateAddress:

    def test_update_promotes_to_default(self, repo):
        addr = make_address(id=3, is_default=False)
        repo.get.return_value = addr

        UserAddressService.update_address(1, 3, {'city': 'Y'}, make_default=True)

        repo.update.assert_called_once_with(addr, {'city': 'Y'})
        repo.clear_default.assert_called_once_with(1)
        repo.set_default.assert_called_once_with(addr)

    def test_update_without_default_change(self, repo):
        addr = make_address(id=3, is_default=False)
        repo.get.return_value = addr

        UserAddressService.update_address(1, 3, {'city': 'Y'}, make_default=None)

        repo.update.assert_called_once_with(addr, {'city': 'Y'})
        repo.clear_default.assert_not_called()
        repo.set_default.assert_not_called()
