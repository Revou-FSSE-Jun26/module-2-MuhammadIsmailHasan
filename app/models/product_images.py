from datetime import datetime
from app.extensions import db


class ProductImage(db.Model):
    __tablename__ = 'product_images'
    __table_args__ = (
        db.CheckConstraint('"order" >= 0', name='ck_product_images_order_non_negative'),
        db.Index('ix_product_images_product_id_order', 'product_id', 'order'),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='CASCADE', name='fk_product_images_product_id'),
        nullable=False,
        index=True,
    )
    url = db.Column(db.String(500), nullable=False)
    order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'url': self.url,
            'order': self.order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
