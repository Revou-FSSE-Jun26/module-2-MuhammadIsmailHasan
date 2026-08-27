"""
Unit tests for CategoryService.

CategoryRepository is mocked so the service logic (duplicate-name checks,
not-found handling, no-op updates) runs in isolation without a database.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services.category_service import (
    CategoryService,
    CategoryNotFoundError,
    CategoryNameExistsError,
)


def make_category(id=1, name='Electronics', is_active=True):
    return SimpleNamespace(id=id, name=name, is_active=is_active)


@pytest.fixture
def repo():
    with patch('app.services.category_service.CategoryRepository') as mock_repo:
        yield mock_repo


class TestGetById:

    def test_success(self, repo):
        repo.get_by_id.return_value = make_category(id=2)
        assert CategoryService.get_by_id(2).id == 2

    def test_not_found(self, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(CategoryNotFoundError):
            CategoryService.get_by_id(2)


class TestCreate:

    def test_success(self, repo):
        repo.find_by_name.return_value = None
        repo.create.return_value = make_category(name='Books')

        result = CategoryService.create({'name': 'Books'})
        assert result.name == 'Books'
        repo.create.assert_called_once_with({'name': 'Books'})

    def test_duplicate_name(self, repo):
        repo.find_by_name.return_value = make_category(name='Books')
        with pytest.raises(CategoryNameExistsError):
            CategoryService.create({'name': 'Books'})
        repo.create.assert_not_called()


class TestUpdate:

    def test_success(self, repo):
        category = make_category(id=1, name='Old')
        repo.get_by_id.return_value = category
        repo.find_by_name.return_value = None
        repo.update.return_value = category

        CategoryService.update(1, {'name': 'New'})
        repo.update.assert_called_once_with(category, {'name': 'New'})

    def test_not_found(self, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(CategoryNotFoundError):
            CategoryService.update(1, {'name': 'New'})

    def test_duplicate_name_excludes_self(self, repo):
        category = make_category(id=1, name='Old')
        repo.get_by_id.return_value = category
        repo.find_by_name.return_value = make_category(id=2, name='New')

        with pytest.raises(CategoryNameExistsError):
            CategoryService.update(1, {'name': 'New'})
        # duplicate check must exclude the current category id
        repo.find_by_name.assert_called_once_with('New', exclude_id=1)

    def test_no_effective_changes_returns_category_without_update(self, repo):
        category = make_category(id=1, name='Old')
        repo.get_by_id.return_value = category

        # all values None -> nothing to update
        result = CategoryService.update(1, {'name': None})
        assert result is category
        repo.update.assert_not_called()
        repo.find_by_name.assert_not_called()


class TestDelete:

    def test_success(self, repo):
        category = make_category(id=1)
        repo.get_by_id.return_value = category

        CategoryService.delete(1)
        repo.soft_delete.assert_called_once_with(category)

    def test_not_found(self, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(CategoryNotFoundError):
            CategoryService.delete(1)
