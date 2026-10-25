from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.models.products import Product
from app.models.sub_categories import SubCategory
from app.models.orders import Order, OrderItem
from app.extensions import db


class ProductRepository:
    @staticmethod
    def get_all(filters=None, sort_by="id", order="asc", page=1, limit=10):
        query = Product.query.options(
            joinedload(Product.sub_category), joinedload(Product.seller)
        ).filter_by(is_active=True)

        if filters:
            if filters.get("name"):
                query = query.filter(Product.name.ilike(f"%{filters['name']}%"))
            if filters.get("sub_category_id"):
                query = query.filter_by(sub_category_id=filters["sub_category_id"])
            if filters.get("seller_id"):
                query = query.filter_by(seller_id=filters["seller_id"])
            if filters.get("min_price") is not None:
                query = query.filter(Product.price >= filters["min_price"])
            if filters.get("max_price") is not None:
                query = query.filter(Product.price <= filters["max_price"])

        if sort_by == "best_selling":
            sold = ProductRepository._sold_subquery()
            sort_column = func.coalesce(sold.c.sold, 0)
            query = query.outerjoin(sold, sold.c.product_id == Product.id)
        else:
            sort_columns = {
                "id": Product.id,
                "name": Product.name,
                "price": Product.price,
                "created_at": Product.created_at,
            }
            sort_column = sort_columns.get(sort_by, Product.id)

        if order == "desc":
            query = query.order_by(sort_column.desc(), Product.id.desc())
        else:
            query = query.order_by(sort_column.asc(), Product.id.asc())

        paginated = query.paginate(page=page, per_page=limit, error_out=False)
        ProductRepository._attach_sold_count(paginated.items)
        return paginated

    @staticmethod
    def _sold_subquery():
        return (
            db.session.query(
                OrderItem.product_id.label("product_id"),
                func.sum(OrderItem.quantity).label("sold"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .filter(
                Order.is_active == True,
                Order.status.notin_(["cancelled", "returned"]),
            )
            .group_by(OrderItem.product_id)
            .subquery()
        )

    @staticmethod
    def _attach_sold_count(products):
        ids = [p.id for p in products]
        counts = {}
        if ids:
            sold = ProductRepository._sold_subquery()
            rows = db.session.query(sold.c.product_id, sold.c.sold).filter(
                sold.c.product_id.in_(ids)
            ).all()
            counts = {pid: int(total) for pid, total in rows}
        for p in products:
            p.sold_count = counts.get(p.id, 0)

    @staticmethod
    def get_by_id(product_id):
        return Product.query.filter_by(id=product_id, is_active=True).first()

    @staticmethod
    def get_by_slug(slug):
        return Product.query.filter_by(slug=slug, is_active=True).first()

    @staticmethod
    def slug_exists(slug):
        return db.session.query(Product.id).filter_by(slug=slug).first() is not None

    @staticmethod
    def create(data, seller_id=None, slug=None):
        product = Product(
            name=data["name"],
            slug=slug,
            description=data.get("description"),
            price=data["price"],
            stock=data.get("stock", 0),
            sub_category_id=data.get("sub_category_id"),
            seller_id=seller_id,
        )
        db.session.add(product)
        db.session.commit()
        return product

    @staticmethod
    def update(product, data):
        if "name" in data:
            product.name = data["name"]
        if "description" in data:
            product.description = data["description"]
        if "price" in data:
            product.price = data["price"]
        if "stock" in data:
            product.stock = data["stock"]
        if "sub_category_id" in data:
            product.sub_category_id = data["sub_category_id"]

        db.session.commit()
        return product

    @staticmethod
    def get_by_sub_category_id(
        sub_category_id, sort_by="id", order="asc", page=1, limit=10
    ):
        query = Product.query.filter_by(sub_category_id=sub_category_id, is_active=True)

        if sort_by == "best_selling":
            sold = ProductRepository._sold_subquery()
            sort_column = func.coalesce(sold.c.sold, 0)
            query = query.outerjoin(sold, sold.c.product_id == Product.id)
        else:
            sort_columns = {
                "id": Product.id,
                "name": Product.name,
                "price": Product.price,
                "created_at": Product.created_at,
            }
            sort_column = sort_columns.get(sort_by, Product.id)

        if order == "desc":
            query = query.order_by(sort_column.desc(), Product.id.desc())
        else:
            query = query.order_by(sort_column.asc(), Product.id.asc())

        paginated = query.paginate(page=page, per_page=limit, error_out=False)
        ProductRepository._attach_sold_count(paginated.items)
        return paginated

    @staticmethod
    def get_by_category_id(category_id, sort_by="id", order="asc", page=1, limit=10):
        query = Product.query.join(
            SubCategory, Product.sub_category_id == SubCategory.id
        ).filter(
            SubCategory.category_id == category_id,
            Product.is_active == True,
            SubCategory.is_active == True,
        )

        if sort_by == "best_selling":
            sold = ProductRepository._sold_subquery()
            sort_column = func.coalesce(sold.c.sold, 0)
            query = query.outerjoin(sold, sold.c.product_id == Product.id)
        else:
            sort_columns = {
                "id": Product.id,
                "name": Product.name,
                "price": Product.price,
                "created_at": Product.created_at,
            }
            sort_column = sort_columns.get(sort_by, Product.id)

        if order == "desc":
            query = query.order_by(sort_column.desc(), Product.id.desc())
        else:
            query = query.order_by(sort_column.asc(), Product.id.asc())

        paginated = query.paginate(page=page, per_page=limit, error_out=False)
        ProductRepository._attach_sold_count(paginated.items)
        return paginated

    @staticmethod
    def soft_delete(product):
        product.is_active = False
        db.session.commit()

    @staticmethod
    def has_active_orders(product_id, active_statuses):
        exists = (
            db.session.query(OrderItem)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(
                OrderItem.product_id == product_id,
                Order.is_active == True,
                Order.status.in_(active_statuses),
            )
            .first()
        )

        return exists is not None
