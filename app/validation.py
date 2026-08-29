from app.models import Category
import re


def is_valid_email(email):
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email or not isinstance(email, str):
        return False
    return EMAIL_REGEX.match(email.strip()) is not None


def validation_category_data(data, required_all=True):
    name = data.get('name')

    if required_all and name is None:
        return "name is required", 400
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            return "name cannot be empty", 400
        if len(name) > 255:
            return "name cannot exceed 255 characters", 422

    return None, None


def validation_products_data(data, required_all=True):
    name = data.get('name')
    price = data.get('price')
    stock = data.get('stock')
    description = data.get('description')
    category_id = data.get('category_id')

    if required_all and name is None:
        return "name is required", 400
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            return "name cannot be empty", 400
        if len(name) > 255:
            return "name cannot exceed 255 characters", 422

    if required_all and price is None:
        return "price is required", 400
    if price is not None:
        if not isinstance(price, (int, float)) or isinstance(price, bool):
            return "price must be a number", 400
        if price > 10**11:
            return "price cannot exceed 11 digits number", 422
        if price < 0:
            return "price cannot be negative", 422

    if required_all and stock is None:
        return "stock is required", 400
    if stock is not None:
        if not isinstance(stock, int) or isinstance(stock, bool):
            return "stock must be number", 400

    if description is not None:
        if len(description) > 1000:
            return "description cannot exceed 1000 characters", 422

    if category_id is not None:
        if not isinstance(category_id, int) or isinstance(category_id, bool):
            return "category_id must be a number", 400
        category = Category.query.filter_by(id=category_id, is_active=True).first()
        if category is None:
            return "category id not found", 404

    return None, None


def validation_users_data(data, required_all=True):
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    if required_all and email is None:
        return "email is required", 400
    if email is not None:
        if not isinstance(email, str) or not email.strip():
            return "email cannot be empty", 400
        if len(email) > 100:
            return "email cannot exceed 100 characters", 422
        if not is_valid_email(email):
            return "invalid email format", 400

    if required_all and username is None:
        return "username is required", 400
    if username is not None:
        if not isinstance(username, str) or not username.strip():
            return "username cannot be empty", 400
        if len(username) > 100:
            return "username cannot exceed 100 characters", 422

    if required_all and password is None:
        return "password is required", 400
    if password is not None:
        if not isinstance(password, str) or not password.strip():
            return "password cannot be empty or must be text", 400

    if required_all and role is None:
        return "role is required", 400
    roles = ('buyer', 'seller')
    if role is not None:
        if not isinstance(role, str) or not role.strip():
            return "role cannot be empty or must be text", 400
        if role not in roles:
            return "user role must be buyer or seller only", 400

    return None, None


def validation_order_data(data):
    items = data.get('items')

    if items is None:
        return "items is required", 400
    if not isinstance(items, list):
        return "items must be a list", 400
    if len(items) == 0:
        return "items cannot be empty", 400

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            return f"item at index {i} must be an object", 400

        product_id = item.get('product_id')
        quantity = item.get('quantity')

        if product_id is None:
            return f"product_id is required for item at index {i}", 400
        if not isinstance(product_id, int) or isinstance(product_id, bool):
            return f"product_id must be a number for item at index {i}", 400

        if quantity is None:
            return f"quantity is required for item at index {i}", 400
        if not isinstance(quantity, int) or isinstance(quantity, bool):
            return f"quantity must be a number for item at index {i}", 400
        if quantity <= 0:
            return f"quantity must be greater than 0 for item at index {i}", 400

    return None, None


ALLOWED_TRANSITIONS = {
    'waiting_for_payment': ['processing'],
    'processing': ['shipped'],
    'shipped': ['delivered'],
    'delivered': [],
    'cancelled': [],
}

UNDELETABLE_STATUSES = ('shipped', 'delivered')
ACTIVE_ORDER_STATUSES = ('waiting_for_payment', 'processing', 'shipped')


def validation_order_status(data, current_status=None):
    status = data.get('status')

    if status is None:
        return "status is required", 400

    valid_statuses = ('waiting_for_payment', 'processing', 'shipped', 'delivered', 'cancelled')
    if status not in valid_statuses:
        return f"status must be one of: {', '.join(valid_statuses)}", 400

    if current_status is not None:
        allowed = ALLOWED_TRANSITIONS.get(current_status, [])
        if status not in allowed:
            return f"cannot change status from '{current_status}' to '{status}'", 400

    return None, None


def validation_delete_order(current_status):
    if current_status in UNDELETABLE_STATUSES:
        return f"cannot delete order with status '{current_status}'", 400

    return None, None
