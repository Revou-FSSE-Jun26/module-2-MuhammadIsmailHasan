"""
Unit tests for SubCategoryService.

SubCategoryRepository and CategoryRepository are mocked so the service logic
(parent-category validation, duplicate-name checks, not-found handling,
no-op updates) runs in isolation without a database.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services.sub_category_service import (
    SubCategoryService,
    SubCategoryNotFoundError,
    SubCategoryNameExistsError,
)
from app.services.category_service import CategoryNotFoundError


def make_sub_category(id=1, name="Laptops", category_id=1, is_active=True):
    return SimpleNamespace(
        id=id, name=name, category_id=category_id, is_active=is_active
    )


def make_category(id=1, name="Electronics", is_active=True):
    return SimpleNamespace(id=id, name=name, is_active=is_active)


@pytest.fixture
def repo():
    with patch("app.services.sub_category_service.SubCategoryRepository") as mock_repo:
        yield mock_repo


@pytest.fixture
def category_repo():
    with patch("app.services.sub_category_service.CategoryRepository") as mock_repo:
        yield mock_repo


class TestGetById:
    def test_success(self, repo):
        repo.get_by_id.return_value = make_sub_category(id=2)
        assert SubCategoryService.get_by_id(2).id == 2

    def test_not_found(self, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(SubCategoryNotFoundError):
            SubCategoryService.get_by_id(2)


class TestCreate:
    def test_success(self, repo, category_repo):
        category_repo.get_by_id.return_value = make_category(id=1)
        repo.find_by_name.return_value = None
        repo.create.return_value = make_sub_category(name="Laptops")

        result = SubCategoryService.create({"name": "Laptops", "category_id": 1})
        assert result.name == "Laptops"
        repo.create.assert_called_once_with({"name": "Laptops", "category_id": 1})

    def test_duplicate_name(self, repo, category_repo):
        category_repo.get_by_id.return_value = make_category(id=1)
        repo.find_by_name.return_value = make_sub_category(name="Laptops")

        with pytest.raises(SubCategoryNameExistsError):
            SubCategoryService.create({"name": "Laptops", "category_id": 1})
        repo.create.assert_not_called()

    def test_parent_not_found(self, repo, category_repo):
        category_repo.get_by_id.return_value = None

        with pytest.raises(CategoryNotFoundError):
            SubCategoryService.create({"name": "Laptops", "category_id": 99})
        repo.find_by_name.assert_not_called()
        repo.create.assert_not_called()

    def test_passes_image_through_to_repository(self, repo, category_repo):
        category_repo.get_by_id.return_value = make_category(id=1)
        repo.find_by_name.return_value = None
        repo.create.return_value = make_sub_category(name="Laptops")

        data = {
            "name": "Laptops",
            "category_id": 1,
            "image": "https://cdn.example.com/s.jpg",
        }
        SubCategoryService.create(data)
        repo.create.assert_called_once_with(data)


class TestUpdate:
    def test_success(self, repo, category_repo):
        sub_category = make_sub_category(id=1, name="Old")
        repo.get_by_id.return_value = sub_category
        repo.find_by_name.return_value = None
        repo.update.return_value = sub_category

        SubCategoryService.update(1, {"name": "New", "category_id": None})
        repo.update.assert_called_once_with(sub_category, {"name": "New"})

    def test_passes_image_through_to_repository(self, repo, category_repo):
        sub_category = make_sub_category(id=1, name="Old")
        repo.get_by_id.return_value = sub_category
        repo.update.return_value = sub_category

        SubCategoryService.update(
            1,
            {
                "name": None,
                "category_id": None,
                "image": "https://cdn.example.com/s.jpg",
            },
        )
        repo.update.assert_called_once_with(
            sub_category, {"image": "https://cdn.example.com/s.jpg"}
        )

    def test_not_found(self, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(SubCategoryNotFoundError):
            SubCategoryService.update(1, {"name": "New", "category_id": None})

    def test_duplicate_name_excludes_self(self, repo, category_repo):
        sub_category = make_sub_category(id=1, name="Old")
        repo.get_by_id.return_value = sub_category
        repo.find_by_name.return_value = make_sub_category(id=2, name="New")

        with pytest.raises(SubCategoryNameExistsError):
            SubCategoryService.update(1, {"name": "New", "category_id": None})
        repo.find_by_name.assert_called_once_with("New", exclude_id=1)

    def test_parent_not_found_on_update(self, repo, category_repo):
        sub_category = make_sub_category(id=1, name="Old")
        repo.get_by_id.return_value = sub_category
        category_repo.get_by_id.return_value = None

        with pytest.raises(CategoryNotFoundError):
            SubCategoryService.update(1, {"name": None, "category_id": 99})
        repo.update.assert_not_called()

    def test_no_effective_changes_returns_without_update(self, repo):
        sub_category = make_sub_category(id=1, name="Old")
        repo.get_by_id.return_value = sub_category

        result = SubCategoryService.update(1, {"name": None, "category_id": None})
        assert result is sub_category
        repo.update.assert_not_called()
        repo.find_by_name.assert_not_called()


class TestGetAllWithProducts:
    def test_delegates_to_repository(self, repo):
        sentinel = object()
        repo.get_all_with_products.return_value = sentinel

        result = SubCategoryService.get_all_with_products(
            filters={"name": "Lap"},
            sort_by="name",
            order="desc",
            page=2,
            limit=5,
        )

        assert result is sentinel
        repo.get_all_with_products.assert_called_once_with(
            filters={"name": "Lap"},
            sort_by="name",
            order="desc",
            page=2,
            limit=5,
        )


class TestDelete:
    def test_success(self, repo):
        sub_category = make_sub_category(id=1)
        repo.get_by_id.return_value = sub_category

        SubCategoryService.delete(1)
        repo.soft_delete.assert_called_once_with(sub_category)

    def test_not_found(self, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(SubCategoryNotFoundError):
            SubCategoryService.delete(1)
