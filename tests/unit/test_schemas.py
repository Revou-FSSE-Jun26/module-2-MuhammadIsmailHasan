"""
Unit tests for marshmallow schemas.

These are pure unit tests: they exercise schema .load() validation in
isolation, with no Flask app, no database, and no HTTP layer.
"""

import pytest
from marshmallow import ValidationError

from app.schemas.category_schema import (
    CreateCategorySchema,
    UpdateCategorySchema,
    CategoryQuerySchema,
)
from app.schemas.product_schema import (
    CreateProductSchema,
    UpdateProductSchema,
    ProductQuerySchema,
)
from app.schemas.order_schema import (
    CreateOrderSchema,
    UpdateOrderStatusSchema,
    OrderQuerySchema,
)
from app.schemas.user_schema import RegisterUserSchema, LoginSchema


class TestCreateCategorySchema:

    def test_valid(self):
        result = CreateCategorySchema().load({'name': 'Books'})
        assert result['name'] == 'Books'

    def test_name_is_stripped(self):
        result = CreateCategorySchema().load({'name': '  Books  '})
        assert result['name'] == 'Books'

    def test_missing_name(self):
        with pytest.raises(ValidationError) as exc:
            CreateCategorySchema().load({})
        assert 'name' in exc.value.messages

    def test_empty_name(self):
        with pytest.raises(ValidationError) as exc:
            CreateCategorySchema().load({'name': ''})
        assert 'name' in exc.value.messages

    def test_whitespace_only_name(self):
        # pre_load turns whitespace-only into None -> null validation error
        with pytest.raises(ValidationError):
            CreateCategorySchema().load({'name': '   '})

    def test_name_too_long(self):
        with pytest.raises(ValidationError) as exc:
            CreateCategorySchema().load({'name': 'x' * 256})
        assert 'name cannot exceed 255 characters' in exc.value.messages['name']


class TestUpdateCategorySchema:

    def test_valid(self):
        result = UpdateCategorySchema().load({'name': 'Updated'})
        assert result['name'] == 'Updated'

    def test_missing_name_required(self):
        with pytest.raises(ValidationError):
            UpdateCategorySchema().load({})


class TestCategoryQuerySchema:

    def test_defaults(self):
        result = CategoryQuerySchema().load({})
        assert result['sort_by'] == 'id'
        assert result['order'] == 'asc'
        assert result['page'] == 1
        assert result['limit'] == 10

    def test_invalid_sort_by(self):
        with pytest.raises(ValidationError):
            CategoryQuerySchema().load({'sort_by': 'unknown'})

    def test_invalid_order(self):
        with pytest.raises(ValidationError):
            CategoryQuerySchema().load({'order': 'sideways'})

    def test_limit_over_max(self):
        with pytest.raises(ValidationError):
            CategoryQuerySchema().load({'limit': 999})


class TestCreateProductSchema:

    def test_valid(self):
        result = CreateProductSchema().load({
            'name': 'Laptop', 'price': 999.99, 'stock': 5,
        })
        assert result['name'] == 'Laptop'
        assert result['price'] == 999.99
        assert result['stock'] == 5

    def test_missing_name(self):
        with pytest.raises(ValidationError) as exc:
            CreateProductSchema().load({'price': 10, 'stock': 1})
        assert 'name is required' in exc.value.messages['name']

    def test_negative_price(self):
        with pytest.raises(ValidationError) as exc:
            CreateProductSchema().load({'name': 'X', 'price': -1, 'stock': 1})
        assert 'price cannot be negative' in exc.value.messages['price']

    def test_price_too_large(self):
        with pytest.raises(ValidationError):
            CreateProductSchema().load({'name': 'X', 'price': 10**12, 'stock': 1})

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            CreateProductSchema().load({
                'name': 'X', 'price': 1, 'stock': 1, 'description': 'd' * 1001,
            })


class TestUpdateProductSchema:

    def test_all_optional(self):
        result = UpdateProductSchema().load({})
        assert result['name'] is None
        assert result['price'] is None

    def test_negative_price_rejected(self):
        with pytest.raises(ValidationError):
            UpdateProductSchema().load({'price': -5})

    def test_none_price_allowed(self):
        result = UpdateProductSchema().load({'price': None})
        assert result['price'] is None


class TestProductQuerySchema:

    def test_defaults(self):
        result = ProductQuerySchema().load({})
        assert result['sort_by'] == 'id'
        assert result['order'] == 'asc'
        assert result['page'] == 1
        assert result['limit'] == 10

    def test_invalid_sort(self):
        with pytest.raises(ValidationError):
            ProductQuerySchema().load({'sort_by': 'color'})


class TestCreateOrderSchema:

    def test_valid(self):
        result = CreateOrderSchema().load({
            'items': [{'product_id': 1, 'quantity': 2}],
        })
        assert len(result['items']) == 1
        assert result['items'][0]['product_id'] == 1
        assert result['items'][0]['quantity'] == 2

    def test_missing_items(self):
        with pytest.raises(ValidationError) as exc:
            CreateOrderSchema().load({})
        assert 'items' in exc.value.messages

    def test_empty_items(self):
        with pytest.raises(ValidationError) as exc:
            CreateOrderSchema().load({'items': []})
        assert 'items' in exc.value.messages

    def test_item_missing_product_id(self):
        with pytest.raises(ValidationError):
            CreateOrderSchema().load({'items': [{'quantity': 1}]})

    def test_item_zero_quantity(self):
        with pytest.raises(ValidationError):
            CreateOrderSchema().load({'items': [{'product_id': 1, 'quantity': 0}]})

    def test_item_negative_quantity(self):
        with pytest.raises(ValidationError):
            CreateOrderSchema().load({'items': [{'product_id': 1, 'quantity': -3}]})


class TestUpdateOrderStatusSchema:

    def test_valid(self):
        result = UpdateOrderStatusSchema().load({'status': 'processing'})
        assert result['status'] == 'processing'

    def test_missing_status(self):
        with pytest.raises(ValidationError):
            UpdateOrderStatusSchema().load({})

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            UpdateOrderStatusSchema().load({'status': 'flying'})


class TestOrderQuerySchema:

    def test_defaults(self):
        result = OrderQuerySchema().load({})
        assert result['sort_by'] == 'id'
        assert result['order'] == 'desc'
        assert result['page'] == 1
        assert result['limit'] == 10
        assert result['include_deleted'] is False
        assert result['status'] is None

    def test_invalid_status_filter(self):
        with pytest.raises(ValidationError):
            OrderQuerySchema().load({'status': 'unknown'})


class TestRegisterUserSchema:

    def test_valid(self):
        result = RegisterUserSchema().load({
            'username': 'newuser', 'email': 'new@test.com',
            'password': 'secret', 'role': 'buyer',
        })
        assert result['username'] == 'newuser'
        assert result['role'] == 'buyer'

    def test_invalid_email(self):
        with pytest.raises(ValidationError) as exc:
            RegisterUserSchema().load({
                'username': 'u', 'email': 'not-email',
                'password': 'secret', 'role': 'buyer',
            })
        assert 'invalid email format' in exc.value.messages['email']

    def test_invalid_role(self):
        with pytest.raises(ValidationError) as exc:
            RegisterUserSchema().load({
                'username': 'u', 'email': 'u@test.com',
                'password': 'secret', 'role': 'admin',
            })
        assert 'buyer or seller only' in exc.value.messages['role'][0]

    def test_missing_fields(self):
        with pytest.raises(ValidationError) as exc:
            RegisterUserSchema().load({'username': 'u'})
        assert 'email' in exc.value.messages
        assert 'password' in exc.value.messages
        assert 'role' in exc.value.messages


class TestLoginSchema:

    def test_valid(self):
        result = LoginSchema().load({'email': 'u@test.com', 'password': 'secret'})
        assert result['email'] == 'u@test.com'

    def test_missing_email(self):
        with pytest.raises(ValidationError) as exc:
            LoginSchema().load({'password': 'secret'})
        assert 'email and password are required' in exc.value.messages['email']

    def test_missing_password(self):
        with pytest.raises(ValidationError) as exc:
            LoginSchema().load({'email': 'u@test.com'})
        assert 'email and password are required' in exc.value.messages['password']
