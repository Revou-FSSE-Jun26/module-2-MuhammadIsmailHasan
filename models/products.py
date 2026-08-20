from datetime import datetime
from helper.utils import db

class Product(db.Model):
    __tablename__ = 'products'
    __table_args__ = (
        db.CheckConstraint('price > 0::numeric'),
    )

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL', name='fk_products_category_id'), index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(1000))
    price = db.Column(db.Numeric(11, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }