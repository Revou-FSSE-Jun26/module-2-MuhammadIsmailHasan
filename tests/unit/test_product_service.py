"""
Unit tests for ProductService.

ProductRepository and the Category model lookup are mocked so the service
logic (category validation, no-op updates, active-order delete guard) runs
in isolation without a database.
"""

from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from app.services.product_service import (
    ProductService,
    ProductNotFoundError,
    CategoryNotFoundError,
    ProductHasActiveOrdersError,
)


def make_product(id=1, name='Laptop'):
    return SimpleNamespace(id=id, name=name)


@pytest.fixture
def repo():
    with patch('app.services.product_service.ProductRepository') as mock_repo:
        mock_repo.slug_exists.return_value = False
        yield mock_repo


@pytest.fixture
def category_model():
    # ProductService references Category.query.filter_by(...).first()
    with patch('app.services.product_service.Category') as mock_cat:
        yield mock_cat


def set_category_lookup(category_model, result):
    category_model.query.filter_by.return_value.first.return_value = result


class TestGetById:

    def test_success(self, repo):
        repo.get_by_id.return_value = make_product(id=2)
        assert ProductService.get_by_id(2).id == 2

    def test_not_found(self, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(ProductNotFoundError):
            ProductService.get_by_id(2)


class TestCreate:

    def test_success_without_category(self, repo, category_model):
        repo.create.return_value = make_product()
        ProductService.create({'name': 'X', 'price': 1, 'stock': 1})
        repo.create.assert_called_once()

    def test_success_with_valid_category(self, repo, category_model):
        set_category_lookup(category_model, SimpleNamespace(id=3))
        repo.create.return_value = make_product()

        ProductService.create({'name': 'X', 'price': 1, 'stock': 1, 'category_id': 3})
        repo.create.assert_called_once()

    def test_seller_id_is_propagated_to_repository(self, repo, category_model):
        repo.create.return_value = make_product()

        ProductService.create({'name': 'X', 'price': 1, 'stock': 1}, seller_id=42)

        assert repo.create.call_args.kwargs['seller_id'] == 42

    def test_slug_generated_from_name(self, repo, category_model):
        repo.create.return_value = make_product()

        ProductService.create({'name': 'Wireless Mouse', 'price': 1, 'stock': 1})

        assert repo.create.call_args.kwargs['slug'] == 'wireless-mouse'

    def test_slug_collision_gets_suffix(self, repo, category_model):
        repo.create.return_value = make_product()
        # first candidate taken, second free
        repo.slug_exists.side_effect = [True, False]

        ProductService.create({'name': 'Wireless Mouse', 'price': 1, 'stock': 1})

        assert repo.create.call_args.kwargs['slug'] == 'wireless-mouse-2'

    def test_invalid_category(self, repo, category_model):
        set_category_lookup(category_model, None)
        with pytest.raises(CategoryNotFoundError):
            ProductService.create({'name': 'X', 'price': 1, 'stock': 1, 'category_id': 99})
        repo.create.assert_not_called()


class TestGetBySlug:

    def test_success(self, repo):
        repo.get_by_slug.return_value = make_product(id=5)
        assert ProductService.get_by_slug('laptop').id == 5

    def test_not_found(self, repo):
        repo.get_by_slug.return_value = None
        with pytest.raises(ProductNotFoundError):
            ProductService.get_by_slug('nope')


class TestUpdate:

    def test_not_found(self, repo, category_model):
        repo.get_by_id.return_value = None
        with pytest.raises(ProductNotFoundError):
            ProductService.update(1, {'name': 'New'})

    def test_no_effective_changes_returns_without_update(self, repo, category_model):
        product = make_product()
        repo.get_by_id.return_value = product

        result = ProductService.update(1, {'name': None, 'price': None})
        assert result is product
        repo.update.assert_not_called()

    def test_invalid_category_on_update(self, repo, category_model):
        repo.get_by_id.return_value = make_product()
        set_category_lookup(category_model, None)

        with pytest.raises(CategoryNotFoundError):
            ProductService.update(1, {'category_id': 99})
        repo.update.assert_not_called()

    def test_valid_update(self, repo, category_model):
        product = make_product()
        repo.get_by_id.return_value = product
        repo.update.return_value = product

        ProductService.update(1, {'name': 'New'})
        repo.update.assert_called_once_with(product, {'name': 'New'})


class TestDelete:

    def test_not_found(self, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(ProductNotFoundError):
            ProductService.delete(1)

    def test_blocked_by_active_orders(self, repo):
        repo.get_by_id.return_value = make_product()
        repo.has_active_orders.return_value = True

        with pytest.raises(ProductHasActiveOrdersError):
            ProductService.delete(1)
        repo.soft_delete.assert_not_called()

    def test_success_when_no_active_orders(self, repo):
        product = make_product()
        repo.get_by_id.return_value = product
        repo.has_active_orders.return_value = False

        ProductService.delete(1)
        repo.soft_delete.assert_called_once_with(product)
