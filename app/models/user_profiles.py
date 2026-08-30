from app.extensions import db
from app.utils.timezone import utcnow


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    __table_args__ = (
        db.UniqueConstraint('user_id', name='uq_user_profiles_user_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE', name='fk_user_profiles_user_id'),
        nullable=False,
        index=True,
    )
    full_name = db.Column(db.String(150))
    phone = db.Column(db.String(30))
    avatar_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'phone': self.phone,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
        }
