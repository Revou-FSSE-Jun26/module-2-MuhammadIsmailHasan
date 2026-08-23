from datetime import datetime
from helper.utils import db

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    role = db.Column(db.String(10), nullable=False, server_default='buyer')
    last_login = db.Column(db.DateTime)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    orders = db.relationship('Order', backref='buyer', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }