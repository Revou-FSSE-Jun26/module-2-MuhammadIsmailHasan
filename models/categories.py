from datetime import datetime
from helper.utils import db

class Category(db.Model):
    __tablename__ = 'categories'
    __table_args__ = (
        db.UniqueConstraint('name', name='uq_categories_name'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    products = db.relationship('Product', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active
        }
        
    def to_dict_detail(self):
        result = self.to_dict()
        result['created_at'] = self.created_at.isoformat() if self.created_at else None
        result['is_active'] = self.is_active
        
        return result
    
    def to_dict_with_products(self):
        result = self.to_dict_detail()
        result['products'] = [product.to_dict() for product in self.products]
        
        return result
