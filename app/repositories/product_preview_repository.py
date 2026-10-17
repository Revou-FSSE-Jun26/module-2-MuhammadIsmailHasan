from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.products import Product
from app.models.sub_categories import SubCategory

DEFAULT_PRODUCTS_LIMIT = 10


class ProductPreviewRepository:

    @staticmethod
    def _fetch(ranked, limit):
        if limit <= 0:
            return []
        wanted = db.session.query(ranked.c.id).filter(ranked.c.rank <= limit)
        return (
            Product.query.options(selectinload(Product.images))
            .filter(Product.id.in_(wanted))
            .order_by(Product.sub_category_id.asc(), Product.id.asc())
            .all()
        )

    @staticmethod
    def by_sub_category(sub_category_ids, limit=DEFAULT_PRODUCTS_LIMIT):
        ids = list(sub_category_ids)
        if not ids or limit <= 0:
            return {}

        ranked = (
            db.session.query(
                Product.id.label("id"),
                func.row_number()
                .over(
                    partition_by=Product.sub_category_id,
                    order_by=Product.id.asc(),
                )
                .label("rank"),
            )
            .filter(Product.is_active.is_(True), Product.sub_category_id.in_(ids))
            .subquery()
        )

        grouped = {sub_category_id: [] for sub_category_id in ids}
        for product in ProductPreviewRepository._fetch(ranked, limit):
            grouped.setdefault(product.sub_category_id, []).append(product)
        return grouped

    @staticmethod
    def by_category(category_ids, limit=DEFAULT_PRODUCTS_LIMIT):
        ids = list(category_ids)
        if not ids or limit <= 0:
            return {}

        ranked = (
            db.session.query(
                Product.id.label("id"),
                SubCategory.category_id.label("category_id"),
                func.row_number()
                .over(
                    partition_by=SubCategory.category_id,
                    order_by=Product.id.asc(),
                )
                .label("rank"),
            )
            .join(SubCategory, Product.sub_category_id == SubCategory.id)
            .filter(
                Product.is_active.is_(True),
                SubCategory.is_active.is_(True),
                SubCategory.category_id.in_(ids),
            )
            .subquery()
        )

        by_sub_category = {}
        for product in ProductPreviewRepository._fetch(ranked, limit):
            by_sub_category.setdefault(product.sub_category_id, []).append(product)

        sub_to_category = dict(
            db.session.query(SubCategory.id, SubCategory.category_id)
            .filter(SubCategory.id.in_(by_sub_category.keys()))
            .all()
        ) if by_sub_category else {}

        grouped = {category_id: [] for category_id in ids}
        for sub_category_id, products in by_sub_category.items():
            category_id = sub_to_category.get(sub_category_id)
            if category_id is not None:
                grouped.setdefault(category_id, []).extend(products)
        return grouped
