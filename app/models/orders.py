from app.extensions import db
from app.utils.timezone import utcnow


class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('waiting_for_payment', 'processing', 'shipped', 'delivered', 'cancelled')",
            name='ck_orders_status_valid'
        ),
        db.CheckConstraint(
            'total_amount >= 0',
            name='ck_orders_total_amount_non_negative'
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT', name='fk_orders_user_id'), nullable=False, index=True)
    total_amount = db.Column(db.Numeric(14, 2), nullable=False)
    status = db.Column(db.String(25), nullable=False, server_default='waiting_for_payment')
    ordered_at = db.Column(db.DateTime, default=utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL', name='fk_orders_updated_by'), nullable=True, index=True)

    shipping_recipient_name = db.Column(db.String(150))
    shipping_phone = db.Column(db.String(30))
    shipping_address_line = db.Column(db.String(255))
    shipping_city = db.Column(db.String(100))
    shipping_postal_code = db.Column(db.String(20))

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    updated_by_user = db.relationship('User', foreign_keys=[updated_by], lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_amount': float(self.total_amount) if self.total_amount is not None else None,
            'status': self.status,
            'ordered_at': self.ordered_at.isoformat() if self.ordered_at else None,
            'updated_by': self.updated_by,
            'shipping_recipient_name': self.shipping_recipient_name,
            'shipping_phone': self.shipping_phone,
            'shipping_address_line': self.shipping_address_line,
            'shipping_city': self.shipping_city,
            'shipping_postal_code': self.shipping_postal_code,
        }

    def to_dict_detail(self):
        result = self.to_dict()
        result['is_active'] = self.is_active
        result['items'] = [item.to_dict() for item in self.items]
        return result


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='ck_order_items_quantity_positive'),
        db.CheckConstraint('unit_price >= 0', name='ck_order_items_unit_price_non_negative'),
        db.CheckConstraint('sub_total >= 0', name='ck_order_items_sub_total_non_negative'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE', name='fk_order_items_order_id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT', name='fk_order_items_product_id'), nullable=False, index=True)
    unit_price = db.Column(db.Numeric(11, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    sub_total = db.Column(db.Numeric(14, 2), nullable=False)

    product = db.relationship('Product', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'unit_price': float(self.unit_price) if self.unit_price is not None else None,
            'quantity': self.quantity,
            'sub_total': float(self.sub_total) if self.sub_total is not None else None
        }
