from app.repositories.user_address_repository import UserAddressRepository


class AddressNotFoundError(Exception):
    pass


class DefaultAddressError(Exception):
    pass


class UserAddressService:

    @staticmethod
    def list_addresses(user_id):
        return UserAddressRepository.list_by_user(user_id)

    @staticmethod
    def get_address(user_id, address_id):
        address = UserAddressRepository.get(user_id, address_id)
        if not address:
            raise AddressNotFoundError("address not found")
        return address

    @staticmethod
    def get_default(user_id):
        return UserAddressRepository.get_default(user_id)

    @staticmethod
    def create_address(user_id, data, make_default=False):
        has_existing = UserAddressRepository.count(user_id) > 0

        should_be_default = make_default or not has_existing

        if should_be_default and has_existing:
            UserAddressRepository.clear_default(user_id)

        return UserAddressRepository.create(user_id, data, is_default=should_be_default)

    @staticmethod
    def update_address(user_id, address_id, data, make_default=None):
        address = UserAddressService.get_address(user_id, address_id)
        UserAddressRepository.update(address, data)

        if make_default is True and not address.is_default:
            UserAddressRepository.clear_default(user_id)
            UserAddressRepository.set_default(address)

        return address

    @staticmethod
    def set_default(user_id, address_id):
        address = UserAddressService.get_address(user_id, address_id)
        if address.is_default:
            return address
        UserAddressRepository.clear_default(user_id)
        return UserAddressRepository.set_default(address)

    @staticmethod
    def delete_address(user_id, address_id):
        address = UserAddressService.get_address(user_id, address_id)

        remaining = UserAddressRepository.count(user_id)
        if address.is_default and remaining > 1:
            raise DefaultAddressError(
                "cannot delete the default address while other addresses exist; "
                "set another address as default first"
            )

        UserAddressRepository.soft_delete(address)
        return address
