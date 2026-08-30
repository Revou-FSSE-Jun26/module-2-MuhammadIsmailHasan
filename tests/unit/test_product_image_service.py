"""
Unit tests for ProductImageService.

ProductImageRepository is mocked so the service logic (product lookup,
admin/seller-owner authorization, image lookup, no-op updates) runs in
isolation without a database.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services.product_image_service import (
    ProductImageService,
    ProductNotFoundError,
    ProductImageNotFoundError,
    ProductImagePermissionError,
)


def make_product(id=1, seller_id=10):
    return SimpleNamespace(id=id, seller_id=seller_id, is_active=True)


def make_image(id=1, product_id=1, url='http://img/1.jpg', order=0):
    return SimpleNamespace(id=id, product_id=product_id, url=url, order=order)


@pytest.fixture
def repo():
    with patch('app.services.product_image_service.ProductImageRepository') as mock_repo:
        yield mock_repo


class TestListImages:

    def test_success(self, repo):
        repo.get_product.return_value = make_product()
        repo.list_by_product.return_value = [make_image(id=1), make_image(id=2)]

        result = ProductImageService.list_images(1)

        assert len(result) == 2
        repo.list_by_product.assert_called_once_with(1)

    def test_product_not_found(self, repo):
        repo.get_product.return_value = None
        with pytest.raises(ProductNotFoundError):
            ProductImageService.list_images(999)


class TestCreate:

    def test_admin_can_create(self, repo):
        repo.get_product.return_value = make_product(seller_id=10)
        repo.create.return_value = make_image()

        ProductImageService.create(
            1, {'url': 'http://img/1.jpg', 'order': 0}, user_id=999, role='admin'
        )

        repo.create.assert_called_once_with(product_id=1, url='http://img/1.jpg', order=0)

    def test_seller_owner_can_create(self, repo):
        repo.get_product.return_value = make_product(seller_id=10)
        repo.create.return_value = make_image()

        ProductImageService.create(
            1, {'url': 'http://img/1.jpg', 'order': 2}, user_id=10, role='seller'
        )

        repo.create.assert_called_once_with(product_id=1, url='http://img/1.jpg', order=2)

    def test_seller_non_owner_forbidden(self, repo):
        repo.get_product.return_value = make_product(seller_id=10)

        with pytest.raises(ProductImagePermissionError):
            ProductImageService.create(
                1, {'url': 'http://img/1.jpg'}, user_id=77, role='seller'
            )
        repo.create.assert_not_called()

    def test_order_defaults_to_zero(self, repo):
        repo.get_product.return_value = make_product(seller_id=10)
        repo.create.return_value = make_image()

        ProductImageService.create(1, {'url': 'http://img/1.jpg'}, user_id=10, role='seller')

        assert repo.create.call_args.kwargs['order'] == 0

    def test_product_not_found(self, repo):
        repo.get_product.return_value = None
        with pytest.raises(ProductNotFoundError):
            ProductImageService.create(999, {'url': 'x'}, user_id=1, role='admin')


class TestUpdate:

    def test_admin_can_update(self, repo):
        repo.get_product.return_value = make_product(seller_id=10)
        image = make_image()
        repo.get_by_id_for_product.return_value = image
        repo.update.return_value = image

        ProductImageService.update(
            1, 5, {'order': 3}, user_id=999, role='admin'
        )

        repo.update.assert_called_once_with(image, {'order': 3})

    def test_seller_owner_can_update(self, repo):
        repo.get_product.return_value = make_product(seller_id=10)
        image = make_image()
        repo.get_by_id_for_product.return_value = image
        repo.update.return_value = image

        ProductImageService.update(1, 5, {'url': 'http://new.jpg'}, user_id=10, role='seller')

        repo.update.assert_called_once_with(image, {'url': 'http://new.jpg'})

    def test_seller_non_owner_forbidden(self, repo):
        repo.get_product.return_value = make_product(seller_id=10)

        with pytest.raises(ProductImagePermissionError):
            ProductImageService.update(1, 5, {'order': 1}, user_id=77, role='seller')
        repo.update.assert_not_called()

    def test_image_not_found(self, repo):
        repo.get_product.return_value = make_product(seller_id=10)
        repo.get_by_id_for_product.return_value = None

        with pytest.raises(ProductImageNotFoundError):
            ProductImageService.update(1, 999, {'order': 1}, user_id=10, role='seller')

    def test_no_effective_changes_returns_without_update(self, repo):
        repo.get_product.return_value = make_product(seller_id=10)
        image = make_image()
        repo.get_by_id_for_product.return_value = image

        result = ProductImageService.update(
            1, 5, {'url': None, 'order': None}, user_id=10, role='seller'
        )

        assert result is image
        repo.update.assert_not_called()

    def test_product_not_found(self, repo):
        repo.get_product.return_value = None
        with pytest.raises(ProductNotFoundError):
            ProductImageService.update(999, 5, {'order': 1}, user_id=1, role='admin')


class TestDelete:

    def test_admin_can_delete(self, repo):
        repo.get_product.return_value = make_product(seller_id=10)
        image = make_image()
        repo.get_by_id_for_product.return_value = image

        ProductImageService.delete(1, 5, user_id=999, role='admin')

        repo.soft_delete.assert_called_once_with(image)

    def test_seller_owner_can_delete(self, repo):
        repo.get_product.return_value = make_product(seller_id=10)
        image = make_image()
        repo.get_by_id_for_product.return_value = image

        ProductImageService.delete(1, 5, user_id=10, role='seller')

        repo.soft_delete.assert_called_once_with(image)

    def test_seller_non_owner_forbidden(self, repo):
        repo.get_product.return_value = make_product(seller_id=10)

        with pytest.raises(ProductImagePermissionError):
            ProductImageService.delete(1, 5, user_id=77, role='seller')
        repo.soft_delete.assert_not_called()

    def test_image_not_found(self, repo):
        repo.get_product.return_value = make_product(seller_id=10)
        repo.get_by_id_for_product.return_value = None

        with pytest.raises(ProductImageNotFoundError):
            ProductImageService.delete(1, 999, user_id=10, role='seller')

    def test_product_not_found(self, repo):
        repo.get_product.return_value = None
        with pytest.raises(ProductNotFoundError):
            ProductImageService.delete(999, 5, user_id=1, role='admin')
