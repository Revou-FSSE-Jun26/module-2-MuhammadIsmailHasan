from app.extensions import db
from app.utils.timezone import utcnow


class Cart(db.Model):
    __tablename__ = 'carts'
    __table_args__ = (
        db.UniqueConstraint('user_id', name='uq_carts_user_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE', name='fk_carts_user_id'),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    items = db.relationship(
        'CartItem',
        backref='cart',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='CartItem.id.asc()',
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
        }


class CartItem(db.Model):
    __tablename__ = 'cart_items'
    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='ck_cart_items_quantity_positive'),
        db.UniqueConstraint('cart_id', 'product_id', name='uq_cart_items_cart_product'),
    )

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(
        db.Integer,
        db.ForeignKey('carts.id', ondelete='CASCADE', name='fk_cart_items_cart_id'),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='RESTRICT', name='fk_cart_items_product_id'),
        nullable=False,
        index=True,
    )
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=utcnow)

    product = db.relationship('Product', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'cart_id': self.cart_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
