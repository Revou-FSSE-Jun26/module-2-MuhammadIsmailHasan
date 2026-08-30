from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import jsonify

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

        return jsonify({
            'message': 'get all categories success',
            'status': True,
            'data': CategoryResponseSchema(many=True).dump(paginated.items),
            'pagination': {
                'page': paginated.page,
                'limit': paginated.per_page,
                'total_items': paginated.total,
                'total_pages': paginated.pages,
            },
        }), 200

    @categories_blp.arguments(CreateCategorySchema)
    @roles_required('seller', 'admin')
    def post(self, validated_data):
        try:
            category = CategoryService.create(validated_data)
        except CategoryNameExistsError as e:
            abort(409, message=str(e))

        return jsonify({
            'message': 'category created',
            'status': True,
            'data': CategoryResponseSchema().dump(category),
        }), 201


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

        return jsonify({
            'message': 'get all categories with products success',
            'status': True,
            'data': CategoryDetailResponseSchema(many=True).dump(paginated.items),
            'pagination': {
                'page': paginated.page,
                'limit': paginated.per_page,
                'total_items': paginated.total,
                'total_pages': paginated.pages,
            },
        }), 200


@categories_blp.route('/<int:category_id>')
class CategoryDetail(MethodView):

    @roles_required('seller', 'buyer', 'admin')
    def get(self, category_id):
        try:
            category = CategoryService.get_by_id(category_id)
        except CategoryNotFoundError as e:
            abort(404, message=str(e))

        return jsonify({
            'message': 'success get category',
            'status': True,
            'data': CategoryDetailResponseSchema().dump(category),
        }), 200

    @categories_blp.arguments(UpdateCategorySchema)
    @roles_required('seller', 'admin')
    def put(self, validated_data, category_id):
        try:
            category = CategoryService.update(category_id, validated_data)
        except CategoryNotFoundError as e:
            abort(404, message=str(e))
        except CategoryNameExistsError as e:
            abort(409, message=str(e))

        return jsonify({
            'message': 'success update category',
            'status': True,
            'data': CategoryResponseSchema().dump(category),
        }), 200

    @roles_required('seller', 'admin')
    def delete(self, category_id):
        try:
            CategoryService.delete(category_id)
        except CategoryNotFoundError as e:
            abort(404, message=str(e))

        return jsonify({
            'message': 'success delete category',
            'status': True,
        }), 200
