from app.repositories.product_repository import ProductRepository
from app.models.categories import Category
from app.validation import ACTIVE_ORDER_STATUSES
from app.slug import slugify


class ProductNotFoundError(Exception):
    pass


class CategoryNotFoundError(Exception):
    pass


class ProductHasActiveOrdersError(Exception):
    pass


class ProductService:

    @staticmethod
    def get_all(filters=None, sort_by='id', order='asc', page=1, limit=10):
        return ProductRepository.get_all(
            filters=filters,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit,
        )

    @staticmethod
    def get_by_id(product_id):
        product = ProductRepository.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError("product not found")
        return product

    @staticmethod
    def get_by_slug(slug):
        product = ProductRepository.get_by_slug(slug)
        if not product:
            raise ProductNotFoundError("product not found")
        return product

    @staticmethod
    def _generate_unique_slug(name):
        base = slugify(name)
        candidate = base
        suffix = 2
        while ProductRepository.slug_exists(candidate):
            candidate = f'{base}-{suffix}'
            suffix += 1
        return candidate

    @staticmethod
    def create(data, seller_id=None):
        if data.get('category_id'):
            category = Category.query.filter_by(
                id=data['category_id'], is_active=True
            ).first()
            if not category:
                raise CategoryNotFoundError("category id not found")

        slug = ProductService._generate_unique_slug(data['name'])

        return ProductRepository.create(data, seller_id=seller_id, slug=slug)

    @staticmethod
    def update(product_id, data):
        product = ProductRepository.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError("Product not found")

        update_data = {k: v for k, v in data.items() if v is not None}

        if not update_data:
            return product

        if 'category_id' in update_data:
            category = Category.query.filter_by(
                id=update_data['category_id'], is_active=True
            ).first()
            if not category:
                raise CategoryNotFoundError("category id not found")

        return ProductRepository.update(product, update_data)

    @staticmethod
    def delete(product_id):
        product = ProductRepository.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError("product not found")

        if ProductRepository.has_active_orders(product_id, ACTIVE_ORDER_STATUSES):
            raise ProductHasActiveOrdersError(
                "cannot delete product: product has active orders"
            )

        ProductRepository.soft_delete(product)
