from app.repositories.product_image_repository import ProductImageRepository


class ProductNotFoundError(Exception):
    pass


class ProductImageNotFoundError(Exception):
    pass


class ProductImagePermissionError(Exception):
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

        return ProductImageRepository.create(
            product_id=product_id,
            url=data['url'],
            order=data.get('order', 0),
        )

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
