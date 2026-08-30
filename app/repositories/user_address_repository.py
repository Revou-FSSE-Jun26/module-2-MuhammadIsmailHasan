from app.models.user_addresses import UserAddress
from app.extensions import db


class UserAddressRepository:

    @staticmethod
    def list_by_user(user_id):
        return (
            UserAddress.query
            .filter_by(user_id=user_id, is_active=True)
            .order_by(UserAddress.is_default.desc(), UserAddress.id.asc())
            .all()
        )

    @staticmethod
    def get(user_id, address_id):
        return UserAddress.query.filter_by(
            id=address_id, user_id=user_id, is_active=True
        ).first()

    @staticmethod
    def get_default(user_id):
        return UserAddress.query.filter_by(
            user_id=user_id, is_default=True, is_active=True
        ).first()

    @staticmethod
    def count(user_id):
        return UserAddress.query.filter_by(user_id=user_id, is_active=True).count()

    @staticmethod
    def create(user_id, data, is_default=False):
        address = UserAddress(
            user_id=user_id,
            label=data.get('label'),
            recipient_name=data['recipient_name'],
            phone=data['phone'],
            address_line=data['address_line'],
            city=data['city'],
            postal_code=data.get('postal_code'),
            is_default=is_default,
        )
        db.session.add(address)
        db.session.commit()
        return address

    @staticmethod
    def update(address, data):
        for field in (
            'label', 'recipient_name', 'phone',
            'address_line', 'city', 'postal_code',
        ):
            if field in data:
                setattr(address, field, data[field])
        db.session.commit()
        return address

    @staticmethod
    def clear_default(user_id):
        UserAddress.query.filter_by(
            user_id=user_id, is_default=True, is_active=True
        ).update({'is_default': False})
        db.session.commit()

    @staticmethod
    def set_default(address):
        address.is_default = True
        db.session.commit()
        return address

    @staticmethod
    def soft_delete(address):
        address.is_active = False
        address.is_default = False
        db.session.commit()
        return address
