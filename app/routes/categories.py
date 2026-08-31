from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.schemas.category_schema import (
    CreateCategorySchema,
    UpdateCategorySchema,
    CategoryQuerySchema,
    CategoryResponseSchema,
    CategoryDetailResponseSchema,
)
from app.services.category_service import (
    CategoryService,
    CategoryNotFoundError,
    CategoryNameExistsError,
)
from app.auth import roles_required
from app.utils.http import make_response, paginate_meta

categories_blp = Blueprint(
    'categories',
    __name__,
    url_prefix='/api/v1/categories',
    description='Category operations',
)


@categories_blp.route('/')
class CategoryList(MethodView):

    @categories_blp.arguments(CategoryQuerySchema, location='query')
    @roles_required('seller', 'buyer', 'admin')
    def get(self, query_params):
        filters = {
            'name': query_params.get('name'),
        }

        paginated = CategoryService.get_all(
            filters=filters,
            sort_by=query_params['sort_by'],
            order=query_params['order'],
            page=query_params['page'],
            limit=query_params['limit'],
        )

        return make_response(
            'get all categories success',
            CategoryResponseSchema(many=True).dump(paginated.items),
            pagination=paginate_meta(paginated),
        )

    @categories_blp.arguments(CreateCategorySchema)
    @roles_required('seller', 'admin')
    def post(self, validated_data):
        try:
            category = CategoryService.create(validated_data)
        except CategoryNameExistsError as e:
            abort(409, message=str(e))

        return make_response(
            'category created',
            CategoryResponseSchema().dump(category),
            201,
        )


@categories_blp.route('/products')
class CategoryListWithProducts(MethodView):

    @categories_blp.arguments(CategoryQuerySchema, location='query')
    @roles_required('seller', 'buyer', 'admin')
    def get(self, query_params):
        filters = {
            'name': query_params.get('name'),
        }

        paginated = CategoryService.get_all(
            filters=filters,
            sort_by=query_params['sort_by'],
            order=query_params['order'],
            page=query_params['page'],
            limit=query_params['limit'],
        )

        return make_response(
            'get all categories with products success',
            CategoryDetailResponseSchema(many=True).dump(paginated.items),
            pagination=paginate_meta(paginated),
        )


@categories_blp.route('/<int:category_id>')
class CategoryDetail(MethodView):

    @roles_required('seller', 'buyer', 'admin')
    def get(self, category_id):
        try:
            category = CategoryService.get_by_id(category_id)
        except CategoryNotFoundError as e:
            abort(404, message=str(e))

        return make_response(
            'success get category',
            CategoryDetailResponseSchema().dump(category),
        )

    @categories_blp.arguments(UpdateCategorySchema)
    @roles_required('seller', 'admin')
    def put(self, validated_data, category_id):
        try:
            category = CategoryService.update(category_id, validated_data)
        except CategoryNotFoundError as e:
            abort(404, message=str(e))
        except CategoryNameExistsError as e:
            abort(409, message=str(e))

        return make_response(
            'success update category',
            CategoryResponseSchema().dump(category),
        )

    @roles_required('seller', 'admin')
    def delete(self, category_id):
        try:
            CategoryService.delete(category_id)
        except CategoryNotFoundError as e:
            abort(404, message=str(e))

        return make_response('success delete category')
