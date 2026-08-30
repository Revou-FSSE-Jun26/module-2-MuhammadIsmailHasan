from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import jsonify
from flask_jwt_extended import get_jwt_identity

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
        current_user_id = int(get_jwt_identity())
        addresses = UserAddressService.list_addresses(current_user_id)

        return jsonify({
            'message': 'get addresses success',
            'status': True,
            'data': AddressResponseSchema(many=True).dump(addresses),
        }), 200

    @addresses_blp.arguments(CreateAddressSchema)
    @roles_required('buyer', 'admin')
    def post(self, validated_data):
        current_user_id = int(get_jwt_identity())
        make_default = validated_data.pop('is_default', False)

        address = UserAddressService.create_address(
            current_user_id, validated_data, make_default=make_default
        )

        return jsonify({
            'message': 'address created',
            'status': True,
            'data': AddressResponseSchema().dump(address),
        }), 201


@addresses_blp.route('/<int:address_id>')
class AddressResource(MethodView):

    @roles_required('buyer', 'admin')
    def get(self, address_id):
        current_user_id = int(get_jwt_identity())

        try:
            address = UserAddressService.get_address(current_user_id, address_id)
        except AddressNotFoundError as e:
            abort(404, message=str(e))

        return jsonify({
            'message': 'get address success',
            'status': True,
            'data': AddressResponseSchema().dump(address),
        }), 200

    @addresses_blp.arguments(UpdateAddressSchema)
    @roles_required('buyer', 'admin')
    def put(self, validated_data, address_id):
        current_user_id = int(get_jwt_identity())
        make_default = validated_data.pop('is_default', None)

        try:
            address = UserAddressService.update_address(
                current_user_id, address_id, validated_data, make_default=make_default
            )
        except AddressNotFoundError as e:
            abort(404, message=str(e))

        return jsonify({
            'message': 'address updated',
            'status': True,
            'data': AddressResponseSchema().dump(address),
        }), 200

    @roles_required('buyer', 'admin')
    def delete(self, address_id):
        current_user_id = int(get_jwt_identity())

        try:
            UserAddressService.delete_address(current_user_id, address_id)
        except AddressNotFoundError as e:
            abort(404, message=str(e))
        except DefaultAddressError as e:
            abort(409, message=str(e))

        return jsonify({
            'message': 'address deleted',
            'status': True,
        }), 200


@addresses_blp.route('/<int:address_id>/default')
class AddressDefault(MethodView):

    @roles_required('buyer', 'admin')
    def put(self, address_id):
        current_user_id = int(get_jwt_identity())

        try:
            address = UserAddressService.set_default(current_user_id, address_id)
        except AddressNotFoundError as e:
            abort(404, message=str(e))

        return jsonify({
            'message': 'default address set',
            'status': True,
            'data': AddressResponseSchema().dump(address),
        }), 200
