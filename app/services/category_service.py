from app.repositories.category_repository import CategoryRepository
from app.services.image_upload import replace_image
from app.repositories.product_preview_repository import (
    DEFAULT_PRODUCTS_LIMIT,
    ProductPreviewRepository,
)


class CategoryNotFoundError(Exception):
    pass


class CategoryNameExistsError(Exception):
    pass


class CategoryService:

    @staticmethod
    def get_all(filters=None, sort_by='id', order='asc', page=1, limit=10):
        return CategoryRepository.get_all(
            filters=filters,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit,
        )

    @staticmethod
    def get_by_id(category_id):
        category = CategoryRepository.get_by_id(category_id)
        if not category:
            raise CategoryNotFoundError("category not found")
        return category

    @staticmethod
    def attach_flat_previews(categories, limit=DEFAULT_PRODUCTS_LIMIT):
        grouped = ProductPreviewRepository.by_category(
            [category.id for category in categories], limit=limit
        )
        for category in categories:
            category.preview_products = grouped.get(category.id, [])
        return categories

    @staticmethod
    def attach_nested_previews(category, limit=DEFAULT_PRODUCTS_LIMIT):
        sub_categories = category.active_sub_categories
        grouped = ProductPreviewRepository.by_sub_category(
            [sub.id for sub in sub_categories], limit=limit
        )
        for sub in sub_categories:
            sub.preview_products = grouped.get(sub.id, [])
        return category

    @staticmethod
    def create(data):
        existing = CategoryRepository.find_by_name(data['name'])
        if existing:
            raise CategoryNameExistsError("category name already exists")

        return CategoryRepository.create(data)

    @staticmethod
    def update(category_id, data):
        category = CategoryRepository.get_by_id(category_id)
        if not category:
            raise CategoryNotFoundError("category not found")

        update_data = {k: v for k, v in data.items() if v is not None}

        if not update_data:
            return category

        if 'name' in update_data:
            duplicate = CategoryRepository.find_by_name(
                update_data['name'], exclude_id=category_id
            )
            if duplicate:
                raise CategoryNameExistsError("category name already exists")

        return CategoryRepository.update(category, update_data)

    @staticmethod
    def delete(category_id):
        category = CategoryRepository.get_by_id(category_id)
        if not category:
            raise CategoryNotFoundError("category not found")

        CategoryRepository.soft_delete(category)

    @staticmethod
    def upload_image(category_id, file_storage):
        category = CategoryRepository.get_by_id(category_id)
        if not category:
            raise CategoryNotFoundError("category not found")

        return replace_image(
            category, "categories", file_storage, CategoryRepository.update
        )
