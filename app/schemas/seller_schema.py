from marshmallow import Schema, fields


class SellerBriefSchema(Schema):
    id = fields.Integer()
    name = fields.String(attribute="username")


def order_seller(order):
    for item in order.items:
        product = item.product
        if product is not None and product.seller is not None:
            return SellerBriefSchema().dump(product.seller)
    return None
