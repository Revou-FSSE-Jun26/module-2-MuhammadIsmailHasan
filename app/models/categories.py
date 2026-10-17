from app.extensions import db
from app.utils.timezone import utcnow
from app.utils.images import build_image_url


class Category(db.Model):
    __tablename__ = "categories"
    __table_args__ = (db.UniqueConstraint("name", name="uq_categories_name"),)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "image": build_image_url(self.image),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
        }

    def to_dict_detail(self):
        result = self.to_dict()
        result["created_at"] = self.created_at.isoformat() if self.created_at else None
        result["is_active"] = self.is_active
        result["sub_categories"] = [
            sub_category.to_dict()
            for sub_category in self.sub_categories
            if sub_category.is_active
        ]

        return result

    @property
    def active_sub_categories(self):
        """Active sub-categories of this category.

        Used by the nested category -> sub_categories -> products schema so the
        tree only exposes active children.
        """
        return [sub for sub in self.sub_categories if sub.is_active]

    @property
    def products(self):
        """Active products reached through this category's active sub-categories.

        Exposed as an attribute so CategoryDetailResponseSchema (which has a
        `products` field) can serialize the product-by-category chain.
        """
        gathered = []
        for sub_category in self.sub_categories:
            if not sub_category.is_active:
                continue
            gathered.extend(
                product for product in sub_category.products if product.is_active
            )
        return gathered

    def to_dict_with_products(self):
        result = self.to_dict_detail()
        result["products"] = [product.to_dict() for product in self.products]

        return result
