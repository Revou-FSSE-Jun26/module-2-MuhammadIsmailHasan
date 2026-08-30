from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services.user_profile_service import (
    UserProfileService,
    ProfileNotFoundError,
)


def make_profile(id=1, user_id=1, full_name='John', phone='123', avatar_url=None):
    return SimpleNamespace(
        id=id, user_id=user_id, full_name=full_name,
        phone=phone, avatar_url=avatar_url,
    )


@pytest.fixture
def repo():
    with patch('app.services.user_profile_service.UserProfileRepository') as mock_repo:
        yield mock_repo


class TestGetProfile:

    def test_get_existing(self, repo):
        profile = make_profile()
        repo.get_by_user_id.return_value = profile

        result = UserProfileService.get(1)

        assert result is profile
        repo.get_by_user_id.assert_called_once_with(1)

    def test_get_missing_raises(self, repo):
        repo.get_by_user_id.return_value = None

        with pytest.raises(ProfileNotFoundError):
            UserProfileService.get(1)


class TestUpsertProfile:

    def test_upsert_creates_when_absent(self, repo):
        repo.get_by_user_id.return_value = None
        repo.create.return_value = make_profile()

        result = UserProfileService.upsert(1, {'full_name': 'John'})

        repo.create.assert_called_once_with(1, {'full_name': 'John'})
        repo.update.assert_not_called()
        assert result is repo.create.return_value

    def test_upsert_updates_when_present(self, repo):
        existing = make_profile()
        repo.get_by_user_id.return_value = existing
        repo.update.return_value = existing

        result = UserProfileService.upsert(1, {'full_name': 'Jane'})

        repo.update.assert_called_once_with(existing, {'full_name': 'Jane'})
        repo.create.assert_not_called()
        assert result is existing
