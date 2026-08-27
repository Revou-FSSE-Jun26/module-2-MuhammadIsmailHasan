"""
Product Service layer.

With flask-smorest:
- Validation is handled by @blp.arguments (schema decorators) in the view
- Service focuses on BUSINESS LOGIC only
- Raises exceptions on failure (view layer catches and responds)
- Returns model objects on success (view layer serializes via @blp.response)
"""

from app.repositories.product_repository import ProductRepository
from app.models.categories import Category
from app.validation import ACTIVE_ORDER_STATUSES


class ProductNotFoundError(Exception):
    """Raised when a product doesn't exist."""
    pass


class CategoryNotFoundError(Exception):
    """Raised when a referenced category doesn't exist."""
    pass


class ProductHasActiveOrdersError(Exception):
    """Raised when trying to delete a product with active orders."""
    pass


class ProductService:
    """
    Service layer — pure business logic.
    No HTTP concepts (no status codes, no jsonify, no request).
    """

    @staticmethod
    def get_all(filters=None, sort_by='id', order='asc', page=1, limit=10):
        """
        Get paginated product list.

        Returns:
            SQLAlchemy Pagination object
        """
        return ProductRepository.get_all(
            filters=filters,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit,
        )

    @staticmethod
    def get_by_id(product_id):
        """
        Get a single product by ID.

        Returns:
            Product model instance

        Raises:
            ProductNotFoundError if not found
        """
        product = ProductRepository.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError("product not found")
        return product

    @staticmethod
    def create(data):
        """
        Validate business rules and create product.

        Args:
            data (dict): Already validated by Marshmallow schema

        Returns:
            Product model instance

        Raises:
            CategoryNotFoundError if category_id doesn't exist
        """
        if data.get('category_id'):
            category = Category.query.filter_by(
                id=data['category_id'], is_active=True
            ).first()
            if not category:
                raise CategoryNotFoundError("category id not found")

        return ProductRepository.create(data)

    @staticmethod
    def update(product_id, data):
        """
        Find product, validate business rules, apply updates.

        Args:
            product_id (int): Product to update
            data (dict): Already validated by Marshmallow schema

        Returns:
            Product model instance

        Raises:
            ProductNotFoundError if product doesn't exist
            CategoryNotFoundError if new category_id doesn't exist
        """
        product = ProductRepository.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError("Product not found")

        # Filter out None values (only update provided fields)
        update_data = {k: v for k, v in data.items() if v is not None}

        if not update_data:
            return product  # nothing to change

        # Business rule: check category exists if being changed
        if 'category_id' in update_data:
            category = Category.query.filter_by(
                id=update_data['category_id'], is_active=True
            ).first()
            if not category:
                raise CategoryNotFoundError("category id not found")

        return ProductRepository.update(product, update_data)

    @staticmethod
    def delete(product_id):
        """
        Check business rules, then soft-delete.

        Raises:
            ProductNotFoundError if product doesn't exist
            ProductHasActiveOrdersError if product has active orders
        """
        product = ProductRepository.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError("product not found")

        if ProductRepository.has_active_orders(product_id, ACTIVE_ORDER_STATUSES):
            raise ProductHasActiveOrdersError(
                "cannot delete product: product has active orders"
            )

        ProductRepository.soft_delete(product)
