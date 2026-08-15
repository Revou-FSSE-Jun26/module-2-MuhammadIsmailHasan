from datetime import datetime
from utils import db

order_items = db.Table(
    'order_items',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True)
)

class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = (
        db.CheckConstraint("status::text = ANY (ARRAY['waitingForPayment'::character varying, 'processing'::character varying, 'shipped'::character varying, 'delivered'::character varying, 'cancelled'::character varying]::text[])"),
        db.CheckConstraint('total_amount >= 0::numeric')
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    total_amount = db.Column(db.Numeric(14, 2), nullable=False)
    status = db.Column(db.String(25), nullable=False, server_default='waitingForPayment')
    ordered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    products = db.relationship('Product', secondary=order_items, backref='orders', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_amount': self.total_amount,
            'status': self.status,
            'ordered_at': self.ordered_at.isoformat() if self.ordered_at else None
        }