from flask.views import MethodView
from flask_smorest import Blueprint, abort

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
from app.utils.auth_context import current_user_id
from app.utils.http import make_response, paginate_meta

products_blp = Blueprint(
    'products',
    __name__,
    url_prefix='/api/v1/products',
    description='Product operations',
)


@products_blp.route('/')
class ProductList(MethodView):

    @products_blp.arguments(ProductQuerySchema, location='query')
    def get(self, query_params):
        filters = {
            'name': query_params.get('name'),
            'category_id': query_params.get('category_id'),
            'seller_id': query_params.get('seller_id'),
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

        return make_response(
            'get all products success',
            ProductResponseSchema(many=True).dump(paginated.items),
            pagination=paginate_meta(paginated),
        )

    @products_blp.arguments(CreateProductSchema)
    @roles_required('seller', 'admin')
    def post(self, validated_data):
        try:
            product = ProductService.create(validated_data, seller_id=current_user_id())
        except CategoryNotFoundError as e:
            abort(404, message=str(e))

        return make_response(
            'product created',
            ProductResponseSchema().dump(product),
            201,
        )


@products_blp.route('/slug/<string:slug>')
class ProductBySlug(MethodView):
    def get(self, slug):
        try:
            product = ProductService.get_by_slug(slug)
        except ProductNotFoundError as e:
            abort(404, message=str(e))

        return make_response(
            'success get product',
            ProductDetailResponseSchema().dump(product),
        )


@products_blp.route('/<int:product_id>')
class ProductDetail(MethodView):

    def get(self, product_id):
        try:
            product = ProductService.get_by_id(product_id)
        except ProductNotFoundError as e:
            abort(404, message=str(e))

        return make_response(
            'success get product',
            ProductDetailResponseSchema().dump(product),
        )

    @products_blp.arguments(UpdateProductSchema)
    @roles_required('seller', 'admin')
    def put(self, validated_data, product_id):
        try:
            product = ProductService.update(product_id, validated_data)
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except CategoryNotFoundError as e:
            abort(404, message=str(e))

        return make_response(
            'success update product',
            ProductResponseSchema().dump(product),
        )

    @roles_required('seller', 'admin')
    def delete(self, product_id):
        try:
            ProductService.delete(product_id)
        except ProductNotFoundError as e:
            abort(404, message=str(e))
        except ProductHasActiveOrdersError as e:
            abort(400, message=str(e))

        return make_response('success delete product')
