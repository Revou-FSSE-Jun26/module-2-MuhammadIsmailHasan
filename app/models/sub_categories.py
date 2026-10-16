from app.extensions import db
from app.utils.timezone import utcnow


class SubCategory(db.Model):
    __tablename__ = 'sub_categories'
    __table_args__ = (
        db.UniqueConstraint('name', name='uq_sub_categories_name'),
    )

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.id', ondelete='SET NULL', name='fk_sub_categories_category_id'),
        index=True,
    )
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    category = db.relationship('Category', backref='sub_categories', lazy=True)
    products = db.relationship('Product', backref='sub_category', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category_id": self.category_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active
        }

    def to_dict_detail(self):
        result = self.to_dict()
        result['category'] = self.category.to_dict() if self.category else None

        return result
