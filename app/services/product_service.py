from app.repositories.product_repository import ProductRepository
from app.models.sub_categories import SubCategory
from app.validation import ACTIVE_ORDER_STATUSES
from app.utils.slug import slugify


class ProductNotFoundError(Exception):
    pass


class CategoryNotFoundError(Exception):
    pass


class SubCategoryNotFoundError(Exception):
    pass


class ProductHasActiveOrdersError(Exception):
    pass


class ProductService:
    @staticmethod
    def get_all(filters=None, sort_by="id", order="asc", page=1, limit=10):
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
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate

    @staticmethod
    def create(data, seller_id=None):
        if data.get("sub_category_id"):
            sub_category = SubCategory.query.filter_by(
                id=data["sub_category_id"], is_active=True
            ).first()
            if not sub_category:
                raise SubCategoryNotFoundError("sub category id not found")

        slug = ProductService._generate_unique_slug(data["name"])

        return ProductRepository.create(data, seller_id=seller_id, slug=slug)

    @staticmethod
    def update(product_id, data):
        product = ProductRepository.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError("Product not found")

        update_data = {k: v for k, v in data.items() if v is not None}

        if not update_data:
            return product

        if "sub_category_id" in update_data:
            sub_category = SubCategory.query.filter_by(
                id=update_data["sub_category_id"], is_active=True
            ).first()
            if not sub_category:
                raise SubCategoryNotFoundError("sub category id not found")

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

    @staticmethod
    def get_by_sub_category_id(
        sub_category_id, sort_by="id", order="asc", page=1, limit=10
    ):
        return ProductRepository.get_by_sub_category_id(
            sub_category_id,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit,
        )

    @staticmethod
    def get_by_category_id(category_id, sort_by="id", order="asc", page=1, limit=10):
        return ProductRepository.get_by_category_id(
            category_id,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit,
        )
