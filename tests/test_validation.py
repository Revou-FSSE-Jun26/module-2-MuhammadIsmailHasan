from helper.validation import (
    validation_category_data,
    validation_products_data,
    validation_users_data,
    validation_order_data,
    validation_order_status,
    validation_delete_order,
    is_valid_email,
    ALLOWED_TRANSITIONS,
    UNDELETABLE_STATUSES,
    ACTIVE_ORDER_STATUSES,
)


class TestIsValidEmail:

    def test_valid_email(self):
        assert is_valid_email('user@example.com') is True

    def test_valid_email_with_dots(self):
        assert is_valid_email('first.last@domain.co.id') is True

    def test_invalid_email_no_at(self):
        assert is_valid_email('userexample.com') is False

    def test_invalid_email_no_domain(self):
        assert is_valid_email('user@') is False

    def test_invalid_email_none(self):
        assert is_valid_email(None) is False

    def test_invalid_email_empty_string(self):
        assert is_valid_email('') is False


class TestValidationCategoryData:

    def test_valid_category(self):
        msg, code = validation_category_data({'name': 'Electronics'})
        assert msg is None
        assert code is None

    def test_missing_name(self):
        msg, code = validation_category_data({})
        assert msg == 'name is required'
        assert code == 400

    def test_empty_name(self):
        msg, code = validation_category_data({'name': ''})
        assert msg == 'name cannot be empty'
        assert code == 400

    def test_name_too_long(self):
        msg, code = validation_category_data({'name': 'x' * 256})
        assert msg == 'name cannot exceed 255 characters'
        assert code == 422

    def test_name_not_required_when_partial(self):
        msg, code = validation_category_data({}, required_all=False)
        assert msg is None
        assert code is None


class TestValidationProductsData:

    def test_valid_product(self):
        data = {'name': 'Laptop', 'price': 999.99, 'stock': 10}
        msg, code = validation_products_data(data)
        assert msg is None

    def test_missing_name(self):
        msg, code = validation_products_data({'price': 10, 'stock': 5})
        assert msg == 'name is required'
        assert code == 400

    def test_missing_price(self):
        msg, code = validation_products_data({'name': 'Test', 'stock': 5})
        assert msg == 'price is required'
        assert code == 400

    def test_missing_stock(self):
        msg, code = validation_products_data({'name': 'Test', 'price': 10})
        assert msg == 'stock is required'
        assert code == 400

    def test_price_not_number(self):
        msg, code = validation_products_data({'name': 'Test', 'price': 'abc', 'stock': 5})
        assert msg == 'price must be a number'
        assert code == 400

    def test_price_negative(self):
        msg, code = validation_products_data({'name': 'Test', 'price': -10, 'stock': 5})
        assert msg == 'price cannot be negative'
        assert code == 422

    def test_price_too_large(self):
        msg, code = validation_products_data({'name': 'Test', 'price': 10**12, 'stock': 5})
        assert msg == 'price cannot exceed 11 digits number'
        assert code == 422

    def test_stock_not_number(self):
        msg, code = validation_products_data({'name': 'Test', 'price': 10, 'stock': 'abc'})
        assert msg == 'stock must be number'
        assert code == 400

    def test_partial_update_valid(self):
        msg, code = validation_products_data({'price': 50.0}, required_all=False)
        assert msg is None


class TestValidationUsersData:

    def test_valid_user(self):
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'pass123',
            'role': 'buyer'
        }
        msg, code = validation_users_data(data)
        assert msg is None

    def test_missing_email(self):
        data = {'username': 'test', 'password': 'pass', 'role': 'buyer'}
        msg, code = validation_users_data(data)
        assert msg == 'email is required'
        assert code == 400

    def test_invalid_email_format(self):
        data = {'email': 'notanemail', 'username': 'test', 'password': 'pass', 'role': 'buyer'}
        msg, code = validation_users_data(data)
        assert msg == 'invalid email format'
        assert code == 400

    def test_missing_username(self):
        data = {'email': 'a@b.com', 'password': 'pass', 'role': 'buyer'}
        msg, code = validation_users_data(data)
        assert msg == 'username is required'
        assert code == 400

    def test_missing_password(self):
        data = {'email': 'a@b.com', 'username': 'test', 'role': 'buyer'}
        msg, code = validation_users_data(data)
        assert msg == 'password is required'
        assert code == 400

    def test_invalid_role(self):
        data = {'email': 'a@b.com', 'username': 'test', 'password': 'pass', 'role': 'admin'}
        msg, code = validation_users_data(data)
        assert msg == 'user role must be buyer or seller only'
        assert code == 400

    def test_valid_seller_role(self):
        data = {'email': 'a@b.com', 'username': 'test', 'password': 'pass', 'role': 'seller'}
        msg, code = validation_users_data(data)
        assert msg is None


class TestValidationOrderData:

    def test_valid_order(self):
        data = {'items': [{'product_id': 1, 'quantity': 2}]}
        msg, code = validation_order_data(data)
        assert msg is None

    def test_missing_items(self):
        msg, code = validation_order_data({})
        assert msg == 'items is required'
        assert code == 400

    def test_items_not_list(self):
        msg, code = validation_order_data({'items': 'not a list'})
        assert msg == 'items must be a list'
        assert code == 400

    def test_items_empty_list(self):
        msg, code = validation_order_data({'items': []})
        assert msg == 'items cannot be empty'
        assert code == 400

    def test_item_missing_product_id(self):
        data = {'items': [{'quantity': 2}]}
        msg, code = validation_order_data(data)
        assert 'product_id is required' in msg
        assert code == 400

    def test_item_missing_quantity(self):
        data = {'items': [{'product_id': 1}]}
        msg, code = validation_order_data(data)
        assert 'quantity is required' in msg
        assert code == 400

    def test_item_quantity_zero(self):
        data = {'items': [{'product_id': 1, 'quantity': 0}]}
        msg, code = validation_order_data(data)
        assert 'must be greater than 0' in msg
        assert code == 400

    def test_item_quantity_negative(self):
        data = {'items': [{'product_id': 1, 'quantity': -1}]}
        msg, code = validation_order_data(data)
        assert 'must be greater than 0' in msg
        assert code == 400


class TestValidationOrderStatus:

    def test_valid_transition_waiting_to_processing(self):
        msg, code = validation_order_status(
            {'status': 'processing'}, current_status='waiting_for_payment'
        )
        assert msg is None

    def test_valid_transition_processing_to_shipped(self):
        msg, code = validation_order_status(
            {'status': 'shipped'}, current_status='processing'
        )
        assert msg is None

    def test_valid_transition_shipped_to_delivered(self):
        msg, code = validation_order_status(
            {'status': 'delivered'}, current_status='shipped'
        )
        assert msg is None

    def test_invalid_skip_waiting_to_shipped(self):
        msg, code = validation_order_status(
            {'status': 'shipped'}, current_status='waiting_for_payment'
        )
        assert 'cannot change status' in msg
        assert code == 400

    def test_invalid_skip_waiting_to_delivered(self):
        msg, code = validation_order_status(
            {'status': 'delivered'}, current_status='waiting_for_payment'
        )
        assert 'cannot change status' in msg
        assert code == 400

    def test_invalid_backward_shipped_to_processing(self):
        msg, code = validation_order_status(
            {'status': 'processing'}, current_status='shipped'
        )
        assert 'cannot change status' in msg
        assert code == 400

    def test_cancel_from_waiting(self):
        msg, code = validation_order_status(
            {'status': 'cancelled'}, current_status='waiting_for_payment'
        )
        assert msg is None

    def test_cancel_from_processing(self):
        msg, code = validation_order_status(
            {'status': 'cancelled'}, current_status='processing'
        )
        assert msg is None

    def test_cannot_cancel_from_shipped(self):
        msg, code = validation_order_status(
            {'status': 'cancelled'}, current_status='shipped'
        )
        assert 'cannot change status' in msg
        assert code == 400

    def test_delivered_is_terminal(self):
        msg, code = validation_order_status(
            {'status': 'processing'}, current_status='delivered'
        )
        assert 'cannot change status' in msg

    def test_missing_status_field(self):
        msg, code = validation_order_status({})
        assert msg == 'status is required'
        assert code == 400

    def test_invalid_status_value(self):
        msg, code = validation_order_status({'status': 'flying'})
        assert 'status must be one of' in msg
        assert code == 400

    def test_no_current_status_skips_transition_check(self):
        msg, code = validation_order_status({'status': 'delivered'}, current_status=None)
        assert msg is None


class TestValidationDeleteOrder:

    def test_can_delete_waiting_for_payment(self):
        msg, code = validation_delete_order('waiting_for_payment')
        assert msg is None

    def test_can_delete_processing(self):
        msg, code = validation_delete_order('processing')
        assert msg is None

    def test_can_delete_cancelled(self):
        msg, code = validation_delete_order('cancelled')
        assert msg is None

    def test_cannot_delete_shipped(self):
        msg, code = validation_delete_order('shipped')
        assert "cannot delete order with status 'shipped'" == msg
        assert code == 400

    def test_cannot_delete_delivered(self):
        msg, code = validation_delete_order('delivered')
        assert "cannot delete order with status 'delivered'" == msg
        assert code == 400


class TestConstants:

    def test_allowed_transitions_keys(self):
        assert set(ALLOWED_TRANSITIONS.keys()) == {
            'waiting_for_payment', 'processing', 'shipped', 'delivered', 'cancelled'
        }

    def test_undeletable_statuses(self):
        assert 'shipped' in UNDELETABLE_STATUSES
        assert 'delivered' in UNDELETABLE_STATUSES
        assert 'waiting_for_payment' not in UNDELETABLE_STATUSES

    def test_active_order_statuses(self):
        assert 'waiting_for_payment' in ACTIVE_ORDER_STATUSES
        assert 'processing' in ACTIVE_ORDER_STATUSES
        assert 'shipped' in ACTIVE_ORDER_STATUSES
        assert 'cancelled' not in ACTIVE_ORDER_STATUSES
        assert 'delivered' not in ACTIVE_ORDER_STATUSES
