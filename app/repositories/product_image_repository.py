from app.models.product_images import ProductImage
from app.models.products import Product
from app.extensions import db


class ProductImageRepository:

    @staticmethod
    def get_product(product_id):
        return Product.query.filter_by(id=product_id, is_active=True).first()

    @staticmethod
    def list_by_product(product_id):
        return (
            ProductImage.query
            .filter_by(product_id=product_id, is_active=True)
            .order_by(ProductImage.order.asc(), ProductImage.id.asc())
            .all()
        )

    @staticmethod
    def get_by_id(image_id):
        return ProductImage.query.filter_by(id=image_id, is_active=True).first()

    @staticmethod
    def get_by_id_for_product(image_id, product_id):
        return ProductImage.query.filter_by(
            id=image_id, product_id=product_id, is_active=True
        ).first()

    @staticmethod
    def get_max_order(product_id):
        return (
            db.session.query(db.func.max(ProductImage.order))
            .filter_by(product_id=product_id, is_active=True)
            .scalar()
        )

    @staticmethod
    def create(product_id, url, order):
        image = ProductImage(product_id=product_id, url=url, order=order)
        db.session.add(image)
        db.session.commit()
        return image

    @staticmethod
    def reorder(images_in_order):
        for position, image in enumerate(images_in_order):
            image.order = position
        db.session.commit()
        return images_in_order

    @staticmethod
    def update(image, data):
        if 'url' in data:
            image.url = data['url']
        if 'order' in data:
            image.order = data['order']
        db.session.commit()
        return image

    @staticmethod
    def soft_delete(image):
        image.is_active = False
        db.session.commit()
