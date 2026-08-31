from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt

from app.schemas.product_image_schema import (
    CreateProductImageSchema,
    UpdateProductImageSchema,
    ReorderImagesSchema,
    ProductImageResponseSchema,
)
from app.services.product_image_service import (
    ProductImageService,
    ProductNotFoundError,
    ProductImageNotFoundError,
    ProductImagePermissionError,
    ReorderValidationError,
)
from app.auth import roles_required

product_images_blp = Blueprint(
    'product_images',
    __name__,
    url_prefix='/api/v1/products/<int:product_id>/images',
    description='Product image operations',
)


@product_images_blp.route('/')
class ProductImageList(MethodView):

    @roles_required('buyer', 'seller', 'admin')
    def get(self, product_id):
        try:
            images = ProductImageService.list_images(product_id)
        except ProductNotFoundError as e:
            abort(404, message=str(e))

        return jsonify({
            'message': 'get all product images success',
            'status': True,
            'data': ProductImageResponseSchema(many=True).dump(images),
        }), 200

    @product_images_blp.arguments(CreateProductImageSchema)
    @roles_required('seller', 'admin')
    def post(self, validated_data, product_id):
        current_user_id = int(get_jwt_identity())
        role = get_jwt().get('role')

        try:
            image = ProductImageService.create(
                product_id, validated_data, user_id=current_user_id, role=role
            )
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except ProductImagePermissionError as e:
            abort(403, message=str(e))

        return jsonify({
            'message': 'product image created',
            'status': True,
            'data': ProductImageResponseSchema().dump(image),
        }), 201


@product_images_blp.route('/<int:image_id>')
class ProductImageDetail(MethodView):

    @product_images_blp.arguments(UpdateProductImageSchema)
    @roles_required('seller', 'admin')
    def put(self, validated_data, product_id, image_id):
        current_user_id = int(get_jwt_identity())
        role = get_jwt().get('role')

        try:
            image = ProductImageService.update(
                product_id, image_id, validated_data,
                user_id=current_user_id, role=role,
            )
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except ProductImageNotFoundError as e:
            abort(404, message=str(e))
        except ProductImagePermissionError as e:
            abort(403, message=str(e))

        return jsonify({
            'message': 'success update product image',
            'status': True,
            'data': ProductImageResponseSchema().dump(image),
        }), 200

    @roles_required('seller', 'admin')
    def delete(self, product_id, image_id):
        current_user_id = int(get_jwt_identity())
        role = get_jwt().get('role')

        try:
            ProductImageService.delete(
                product_id, image_id, user_id=current_user_id, role=role
            )
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except ProductImageNotFoundError as e:
            abort(404, message=str(e))
        except ProductImagePermissionError as e:
            abort(403, message=str(e))

        return jsonify({
            'message': 'success delete product image',
            'status': True,
        }), 200


@product_images_blp.route('/reorder')
class ProductImageReorder(MethodView):

    @product_images_blp.arguments(ReorderImagesSchema)
    @roles_required('seller', 'admin')
    def put(self, validated_data, product_id):
        current_user_id = int(get_jwt_identity())
        role = get_jwt().get('role')

        try:
            images = ProductImageService.reorder(
                product_id, validated_data['image_ids'],
                user_id=current_user_id, role=role,
            )
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except ProductImagePermissionError as e:
            abort(403, message=str(e))
        except ReorderValidationError as e:
            abort(422, message=str(e))

        return jsonify({
            'message': 'product images reordered',
            'status': True,
            'data': ProductImageResponseSchema(many=True).dump(images),
        }), 200
