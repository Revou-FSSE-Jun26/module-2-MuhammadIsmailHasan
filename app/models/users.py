from app.extensions import db
from app.utils.timezone import utcnow


class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        db.CheckConstraint(
            "role IN ('buyer', 'seller', 'admin')",
            name='ck_users_role_valid'
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    role = db.Column(db.String(10), nullable=False, server_default='buyer')
    last_login = db.Column(db.DateTime)

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    orders = db.relationship('Order', backref='buyer', lazy=True, foreign_keys='Order.user_id')

    profile = db.relationship(
        'UserProfile',
        backref='user',
        uselist=False,
        lazy=True,
        cascade='all, delete-orphan',
    )
    addresses = db.relationship(
        'UserAddress',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='UserAddress.id.asc()',
    )

    def to_dict_public(self):
        return {
            'username': self.username,
            'email': self.email
        }

    def to_dict(self):
        result = self.to_dict_public()
        result['id'] = self.id
        result['role'] = self.role
        result['last_login'] = self.last_login.isoformat() if self.last_login else None
        result['created_at'] = self.created_at.isoformat() if self.created_at else None

        return result
