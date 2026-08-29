from datetime import datetime
from app.extensions import db


class Product(db.Model):
    __tablename__ = 'products'
    __table_args__ = (
        db.CheckConstraint('price >= 0', name='ck_products_price_non_negative'),
    )

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL', name='fk_products_category_id'), index=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL', name='fk_products_seller_id'), nullable=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(1000))
    price = db.Column(db.Numeric(11, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    seller = db.relationship('User', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': float(self.price) if self.price is not None else None,
            'stock': self.stock,
        }

    def to_dict_detail(self):
        result = self.to_dict()
        result['description'] = self.description
        result['seller_id'] = self.seller_id
        result['created_at'] = self.created_at.isoformat() if self.created_at else None
        result['is_active'] = self.is_active
        result['category'] = self.category.to_dict() if self.category else None

        return result
