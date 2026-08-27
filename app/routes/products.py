from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import jsonify

from app.schemas.product_schema import (
    CreateProductSchema,
    UpdateProductSchema,
    ProductQuerySchema,
    ProductResponseSchema,
    ProductDetailResponseSchema,
)
from app.services.product_service import (
    ProductService,
    ProductNotFoundError,
    CategoryNotFoundError,
    ProductHasActiveOrdersError,
)
from app.auth import roles_required

products_blp = Blueprint(
    'products',
    __name__,
    url_prefix='/api/v1/products',
    description='Product operations',
)


@products_blp.route('/')
class ProductList(MethodView):

    @products_blp.arguments(ProductQuerySchema, location='query')
    @roles_required('buyer', 'seller', 'admin')
    def get(self, query_params):
        filters = {
            'name': query_params.get('name'),
            'category_id': query_params.get('category_id'),
            'min_price': query_params.get('min_price'),
            'max_price': query_params.get('max_price'),
        }

        paginated = ProductService.get_all(
            filters=filters,
            sort_by=query_params['sort_by'],
            order=query_params['order'],
            page=query_params['page'],
            limit=query_params['limit'],
        )

        return jsonify({
            'message': 'get all products success',
            'status': True,
            'data': ProductResponseSchema(many=True).dump(paginated.items),
            'pagination': {
                'page': paginated.page,
                'limit': paginated.per_page,
                'total_items': paginated.total,
                'total_pages': paginated.pages,
            },
        }), 200

    @products_blp.arguments(CreateProductSchema)
    @roles_required('seller', 'admin')
    def post(self, validated_data):
        try:
            product = ProductService.create(validated_data)
        except CategoryNotFoundError as e:
            abort(404, message=str(e))

        return jsonify({
            'message': 'product created',
            'status': True,
            'data': ProductResponseSchema().dump(product),
        }), 201


@products_blp.route('/<int:product_id>')
class ProductDetail(MethodView):

    @roles_required('seller', 'buyer', 'admin')
    def get(self, product_id):
        try:
            product = ProductService.get_by_id(product_id)
        except ProductNotFoundError as e:
            abort(404, message=str(e))

        return jsonify({
            'message': 'success get product',
            'status': True,
            'data': ProductDetailResponseSchema().dump(product),
        }), 200

    @products_blp.arguments(UpdateProductSchema)
    @roles_required('seller', 'admin')
    def put(self, validated_data, product_id):
        try:
            product = ProductService.update(product_id, validated_data)
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except CategoryNotFoundError as e:
            abort(404, message=str(e))

        return jsonify({
            'message': 'success update product',
            'status': True,
            'data': ProductResponseSchema().dump(product),
        }), 200

    @roles_required('seller', 'admin')
    def delete(self, product_id):
        try:
            ProductService.delete(product_id)
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except ProductHasActiveOrdersError as e:
            abort(400, message=str(e))

        return jsonify({
            'message': 'success delete product',
            'status': True,
        }), 200
