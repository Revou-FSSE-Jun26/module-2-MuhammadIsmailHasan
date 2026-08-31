from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.schemas.user_address_schema import (
    CreateAddressSchema,
    UpdateAddressSchema,
    AddressResponseSchema,
)
from app.services.user_address_service import (
    UserAddressService,
    AddressNotFoundError,
    DefaultAddressError,
)
from app.auth import roles_required
from app.utils.auth_context import current_user_id
from app.utils.http import make_response

addresses_blp = Blueprint(
    'addresses',
    __name__,
    url_prefix='/api/v1/addresses',
    description='Shipping address book (buyer)',
)


@addresses_blp.route('')
class AddressList(MethodView):

    @roles_required('buyer', 'admin')
    def get(self):
        addresses = UserAddressService.list_addresses(current_user_id())

        return make_response(
            'get addresses success',
            AddressResponseSchema(many=True).dump(addresses),
        )

    @addresses_blp.arguments(CreateAddressSchema)
    @roles_required('buyer', 'admin')
    def post(self, validated_data):
        make_default = validated_data.pop('is_default', False)

        address = UserAddressService.create_address(
            current_user_id(), validated_data, make_default=make_default
        )

        return make_response(
            'address created',
            AddressResponseSchema().dump(address),
            201,
        )


@addresses_blp.route('/<int:address_id>')
class AddressResource(MethodView):

    @roles_required('buyer', 'admin')
    def get(self, address_id):
        try:
            address = UserAddressService.get_address(current_user_id(), address_id)
        except AddressNotFoundError as e:
            abort(404, message=str(e))

        return make_response(
            'get address success',
            AddressResponseSchema().dump(address),
        )

    @addresses_blp.arguments(UpdateAddressSchema)
    @roles_required('buyer', 'admin')
    def put(self, validated_data, address_id):
        make_default = validated_data.pop('is_default', None)

        try:
            address = UserAddressService.update_address(
                current_user_id(), address_id, validated_data, make_default=make_default
            )
        except AddressNotFoundError as e:
            abort(404, message=str(e))

        return make_response(
            'address updated',
            AddressResponseSchema().dump(address),
        )

    @roles_required('buyer', 'admin')
    def delete(self, address_id):
        try:
            UserAddressService.delete_address(current_user_id(), address_id)
        except AddressNotFoundError as e:
            abort(404, message=str(e))
        except DefaultAddressError as e:
            abort(409, message=str(e))

        return make_response('address deleted')


@addresses_blp.route('/<int:address_id>/default')
class AddressDefault(MethodView):

    @roles_required('buyer', 'admin')
    def put(self, address_id):
        try:
            address = UserAddressService.set_default(current_user_id(), address_id)
        except AddressNotFoundError as e:
            abort(404, message=str(e))

        return make_response(
            'default address set',
            AddressResponseSchema().dump(address),
        )
