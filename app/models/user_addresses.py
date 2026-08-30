from app.extensions import db
from app.utils.timezone import utcnow


class UserAddress(db.Model):
    __tablename__ = 'user_addresses'
    __table_args__ = (
        db.Index(
            'uq_user_addresses_one_default',
            'user_id',
            unique=True,
            sqlite_where=db.text('is_default = 1'),
            postgresql_where=db.text('is_default = true'),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE', name='fk_user_addresses_user_id'),
        nullable=False,
        index=True,
    )
    label = db.Column(db.String(50))
    recipient_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    address_line = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20))
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'label': self.label,
            'recipient_name': self.recipient_name,
            'phone': self.phone,
            'address_line': self.address_line,
            'city': self.city,
            'postal_code': self.postal_code,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
        }
