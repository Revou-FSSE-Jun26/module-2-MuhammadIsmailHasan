from flask.views import MethodView
from flask_smorest import Blueprint, abort

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
from app.utils.auth_context import current_user_id, current_role
from app.utils.http import make_response

product_images_blp = Blueprint(
    'product_images',
    __name__,
    url_prefix='/api/v1/products/<int:product_id>/images',
    description='Product image operations',
)


@product_images_blp.route('/')
class ProductImageList(MethodView):

    def get(self, product_id):
        try:
            images = ProductImageService.list_images(product_id)
        except ProductNotFoundError as e:
            abort(404, message=str(e))

        return make_response(
            'get all product images success',
            ProductImageResponseSchema(many=True).dump(images),
        )

    @product_images_blp.arguments(CreateProductImageSchema)
    @roles_required('seller', 'admin')
    def post(self, validated_data, product_id):
        try:
            image = ProductImageService.create(
                product_id, validated_data,
                user_id=current_user_id(), role=current_role(),
            )
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except ProductImagePermissionError as e:
            abort(403, message=str(e))

        return make_response(
            'product image created',
            ProductImageResponseSchema().dump(image),
            201,
        )


@product_images_blp.route('/<int:image_id>')
class ProductImageDetail(MethodView):

    @product_images_blp.arguments(UpdateProductImageSchema)
    @roles_required('seller', 'admin')
    def put(self, validated_data, product_id, image_id):
        try:
            image = ProductImageService.update(
                product_id, image_id, validated_data,
                user_id=current_user_id(), role=current_role(),
            )
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except ProductImageNotFoundError as e:
            abort(404, message=str(e))
        except ProductImagePermissionError as e:
            abort(403, message=str(e))

        return make_response(
            'success update product image',
            ProductImageResponseSchema().dump(image),
        )

    @roles_required('seller', 'admin')
    def delete(self, product_id, image_id):
        try:
            ProductImageService.delete(
                product_id, image_id,
                user_id=current_user_id(), role=current_role(),
            )
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except ProductImageNotFoundError as e:
            abort(404, message=str(e))
        except ProductImagePermissionError as e:
            abort(403, message=str(e))

        return make_response('success delete product image')


@product_images_blp.route('/reorder')
class ProductImageReorder(MethodView):

    @product_images_blp.arguments(ReorderImagesSchema)
    @roles_required('seller', 'admin')
    def put(self, validated_data, product_id):
        try:
            images = ProductImageService.reorder(
                product_id, validated_data['image_ids'],
                user_id=current_user_id(), role=current_role(),
            )
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except ProductImagePermissionError as e:
            abort(403, message=str(e))
        except ReorderValidationError as e:
            abort(422, message=str(e))

        return make_response(
            'product images reordered',
            ProductImageResponseSchema(many=True).dump(images),
        )
