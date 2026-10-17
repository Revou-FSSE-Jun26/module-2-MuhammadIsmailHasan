from marshmallow import Schema, fields, validate

from app.repositories.product_preview_repository import DEFAULT_PRODUCTS_LIMIT

PREVIEW_ATTRIBUTE = "preview_products"


def preview_products(obj):
    products = getattr(obj, PREVIEW_ATTRIBUTE, None)
    if products is not None:
        return products
    return getattr(obj, "active_products", [])


class ProductsLimitQuerySchema(Schema):
    products_limit = fields.Integer(
        load_default=DEFAULT_PRODUCTS_LIMIT, validate=validate.Range(min=0, max=100)
    )
