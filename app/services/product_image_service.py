from flask import current_app

from app.integrations import s3
from app.integrations.s3 import ImageStorageError
from app.repositories.product_image_repository import ProductImageRepository
from app.utils.images import validate_image_upload


class ProductNotFoundError(Exception):
    pass


class ProductImageNotFoundError(Exception):
    pass


class ProductImagePermissionError(Exception):
    pass


class ReorderValidationError(Exception):
    pass


class ProductImageService:

    @staticmethod
    def _get_product_or_404(product_id):
        product = ProductImageRepository.get_product(product_id)
        if not product:
            raise ProductNotFoundError("product not found")
        return product

    @staticmethod
    def _authorize(product, user_id, role):
        if role == 'admin':
            return
        if role == 'seller' and product.seller_id == user_id:
            return
        raise ProductImagePermissionError(
            "you don't have permission to manage images for this product"
        )

    @staticmethod
    def list_images(product_id):
        ProductImageService._get_product_or_404(product_id)
        return ProductImageRepository.list_by_product(product_id)

    @staticmethod
    def create(product_id, data, user_id=None, role=None):
        product = ProductImageService._get_product_or_404(product_id)
        ProductImageService._authorize(product, user_id, role)

        max_order = ProductImageRepository.get_max_order(product_id)
        next_order = 0 if max_order is None else max_order + 1

        return ProductImageRepository.create(
            product_id=product_id,
            url=data['url'],
            order=next_order,
        )

    @staticmethod
    def create_from_upload(product_id, file_storage, user_id=None, role=None):
        product = ProductImageService._get_product_or_404(product_id)
        ProductImageService._authorize(product, user_id, role)

        if not s3.is_configured():
            raise ImageStorageError("image storage is not configured")

        extension, content_type = validate_image_upload(
            file_storage, current_app.config["MAX_IMAGE_UPLOAD_BYTES"]
        )

        key = s3.build_product_key(product_id, extension)
        s3.upload(file_storage.stream, key, content_type)

        try:
            max_order = ProductImageRepository.get_max_order(product_id)
            next_order = 0 if max_order is None else max_order + 1
            return ProductImageRepository.create(
                product_id=product_id, url=key, order=next_order
            )
        except Exception:
            s3.delete(key)
            raise

    @staticmethod
    def update(product_id, image_id, data, user_id=None, role=None):
        product = ProductImageService._get_product_or_404(product_id)
        ProductImageService._authorize(product, user_id, role)

        image = ProductImageRepository.get_by_id_for_product(image_id, product_id)
        if not image:
            raise ProductImageNotFoundError("product image not found")

        update_data = {k: v for k, v in data.items() if v is not None}
        if not update_data:
            return image

        return ProductImageRepository.update(image, update_data)

    @staticmethod
    def delete(product_id, image_id, user_id=None, role=None):
        product = ProductImageService._get_product_or_404(product_id)
        ProductImageService._authorize(product, user_id, role)

        image = ProductImageRepository.get_by_id_for_product(image_id, product_id)
        if not image:
            raise ProductImageNotFoundError("product image not found")

        ProductImageRepository.soft_delete(image)

    @staticmethod
    def reorder(product_id, image_ids, user_id=None, role=None):
        product = ProductImageService._get_product_or_404(product_id)
        ProductImageService._authorize(product, user_id, role)

        images = ProductImageRepository.list_by_product(product_id)
        existing_ids = [img.id for img in images]

        if len(image_ids) != len(set(image_ids)):
            raise ReorderValidationError("image_ids cannot contain duplicates")

        if set(image_ids) != set(existing_ids):
            raise ReorderValidationError(
                "image_ids must contain exactly the product's active image ids"
            )

        by_id = {img.id: img for img in images}
        ordered = [by_id[iid] for iid in image_ids]

        return ProductImageRepository.reorder(ordered)
