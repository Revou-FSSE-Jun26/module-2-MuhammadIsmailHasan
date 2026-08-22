from datetime import datetime
from helper.utils import db

order_items = db.Table(
    'order_items',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id', name='fk_order_items_order_id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id', name='fk_order_items_product_id'), primary_key=True)
)

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
    ordered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    products = db.relationship('Product', secondary=order_items, backref='orders', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_amount': self.total_amount,
            'status': self.status,
            'ordered_at': self.ordered_at.isoformat() if self.ordered_at else None
        }