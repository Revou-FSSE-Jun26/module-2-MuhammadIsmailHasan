from app.repositories.sub_category_repository import SubCategoryRepository
from app.repositories.category_repository import CategoryRepository
from app.services.category_service import CategoryNotFoundError


class SubCategoryNotFoundError(Exception):
    pass


class SubCategoryNameExistsError(Exception):
    pass


class SubCategoryService:

    @staticmethod
    def get_all(filters=None, sort_by='id', order='asc', page=1, limit=10):
        return SubCategoryRepository.get_all(
            filters=filters,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit,
        )

    @staticmethod
    def get_by_id(sub_category_id):
        sub_category = SubCategoryRepository.get_by_id(sub_category_id)
        if not sub_category:
            raise SubCategoryNotFoundError("sub category not found")
        return sub_category

    @staticmethod
    def create(data):
        category = CategoryRepository.get_by_id(data['category_id'])
        if not category:
            raise CategoryNotFoundError("category id not found")

        existing = SubCategoryRepository.find_by_name(data['name'])
        if existing:
            raise SubCategoryNameExistsError("sub category name already exists")

        return SubCategoryRepository.create(data)

    @staticmethod
    def update(sub_category_id, data):
        sub_category = SubCategoryRepository.get_by_id(sub_category_id)
        if not sub_category:
            raise SubCategoryNotFoundError("sub category not found")

        update_data = {k: v for k, v in data.items() if v is not None}

        if not update_data:
            return sub_category

        if 'category_id' in update_data:
            category = CategoryRepository.get_by_id(update_data['category_id'])
            if not category:
                raise CategoryNotFoundError("category id not found")

        if 'name' in update_data:
            duplicate = SubCategoryRepository.find_by_name(
                update_data['name'], exclude_id=sub_category_id
            )
            if duplicate:
                raise SubCategoryNameExistsError("sub category name already exists")

        return SubCategoryRepository.update(sub_category, update_data)

    @staticmethod
    def delete(sub_category_id):
        sub_category = SubCategoryRepository.get_by_id(sub_category_id)
        if not sub_category:
            raise SubCategoryNotFoundError("sub category not found")

        SubCategoryRepository.soft_delete(sub_category)
