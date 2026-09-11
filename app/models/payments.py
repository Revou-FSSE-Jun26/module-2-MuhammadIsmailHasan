from app.extensions import db
from app.utils.timezone import utcnow

class Payment(db.Model):
    __tablename__ = 'payments'
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('pending', 'paid', 'expired', 'failed', 'refunded')",
            name='ck_payments_status_valid'
        ),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='RESTRICT', name='fk_payment_order_id'), nullable=False, index=True)
    payment_reference = db.Column(db.String(255), unique=True, nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    status = db.Column(db.String(25), nullable=False, server_default='pending')
    payment_method = db.Column(db.String(15))
    transaction_time = db.Column(db.DateTime)
    settlement_time = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime, nullable=False)
    raw_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, onupdate=utcnow)

    order = db.relationship('Order', back_populates='payments', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'payment_reference': self.payment_reference,
            'amount': float(self.amount) if self.amount is not None else None,
            'status': self.status,
            'payment_method': self.payment_method,
            'transaction_time': self.transaction_time.isoformat() if self.transaction_time is not None else None,
            'settlement_time': self.settlement_time.isoformat() if self.settlement_time is not None else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at is not None else None,
            'raw_response' : self.raw_response if self.raw_response is not None else None,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None,
        }
    
    
    