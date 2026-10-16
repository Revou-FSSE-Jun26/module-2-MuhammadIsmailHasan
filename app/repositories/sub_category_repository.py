from sqlalchemy.orm import selectinload

from app.models.sub_categories import SubCategory
from app.extensions import db


class SubCategoryRepository:
    @staticmethod
    def _apply_filters_and_sort(query, filters, sort_by, order):
        if filters:
            if filters.get("name"):
                query = query.filter(SubCategory.name.ilike(f"%{filters['name']}%"))
            if filters.get("category_id"):
                query = query.filter_by(category_id=filters["category_id"])

        sort_columns = {
            "id": SubCategory.id,
            "name": SubCategory.name,
            "created_at": SubCategory.created_at,
        }
        sort_column = sort_columns.get(sort_by, SubCategory.id)

        if order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        return query

    @staticmethod
    def get_all(filters=None, sort_by="id", order="asc", page=1, limit=10):
        query = SubCategory.query.filter_by(is_active=True)
        query = SubCategoryRepository._apply_filters_and_sort(
            query, filters, sort_by, order
        )

        return query.paginate(page=page, per_page=limit, error_out=False)

    @staticmethod
    def get_all_with_products(
        filters=None, sort_by="id", order="asc", page=1, limit=10
    ):
        """Paginated active sub-categories with their products eager-loaded.

        Products are eager-loaded with ``selectinload`` to avoid an N+1 query
        when the nested schema reads each sub-category's ``active_products``.
        """
        query = SubCategory.query.filter_by(is_active=True).options(
            selectinload(SubCategory.products)
        )
        query = SubCategoryRepository._apply_filters_and_sort(
            query, filters, sort_by, order
        )

        return query.paginate(page=page, per_page=limit, error_out=False)

    @staticmethod
    def get_by_id(sub_category_id):
        return SubCategory.query.filter_by(id=sub_category_id, is_active=True).first()

    @staticmethod
    def find_by_name(name, exclude_id=None):
        query = SubCategory.query.filter_by(name=name, is_active=True)
        if exclude_id is not None:
            query = query.filter(SubCategory.id != exclude_id)
        return query.first()

    @staticmethod
    def create(data):
        sub_category = SubCategory(
            name=data["name"],
            category_id=data["category_id"],
            image=data.get("image"),
        )
        db.session.add(sub_category)
        db.session.commit()
        return sub_category

    @staticmethod
    def update(sub_category, data):
        if "name" in data:
            sub_category.name = data["name"]
        if "category_id" in data:
            sub_category.category_id = data["category_id"]
        if "image" in data:
            sub_category.image = data["image"]

        db.session.commit()
        return sub_category

    @staticmethod
    def soft_delete(sub_category):
        sub_category.is_active = False
        db.session.commit()

    @staticmethod
    def get_by_category_id(category_id):
        return SubCategory.query.filter_by(
            category_id=category_id, is_active=True
        ).all()
