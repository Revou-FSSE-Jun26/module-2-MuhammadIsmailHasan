from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.schemas.sub_category_schema import (
    CreateSubCategorySchema,
    UpdateSubCategorySchema,
    SubCategoryQuerySchema,
    SubCategoryResponseSchema,
    SubCategoryDetailResponseSchema,
)
from app.schemas.category_schema import SubCategoryWithProductsSchema
from app.services.sub_category_service import (
    SubCategoryService,
    SubCategoryNotFoundError,
    SubCategoryNameExistsError,
)
from app.services.category_service import CategoryNotFoundError
from app.auth import roles_required
from app.utils.http import make_response, paginate_meta

sub_categories_blp = Blueprint(
    "sub_categories",
    __name__,
    url_prefix="/api/v1/sub-categories",
    description="Sub-category operations",
)


@sub_categories_blp.route("/")
class SubCategoryList(MethodView):
    @sub_categories_blp.arguments(SubCategoryQuerySchema, location="query")
    def get(self, query_params):
        filters = {
            "name": query_params.get("name"),
            "category_id": query_params.get("category_id"),
        }

        paginated = SubCategoryService.get_all(
            filters=filters,
            sort_by=query_params["sort_by"],
            order=query_params["order"],
            page=query_params["page"],
            limit=query_params["limit"],
        )

        return make_response(
            "get all sub categories success",
            SubCategoryResponseSchema(many=True).dump(paginated.items),
            pagination=paginate_meta(paginated),
        )

    @sub_categories_blp.arguments(CreateSubCategorySchema)
    @roles_required("seller", "admin")
    def post(self, validated_data):
        try:
            sub_category = SubCategoryService.create(validated_data)
        except CategoryNotFoundError as e:
            abort(404, message=str(e))
        except SubCategoryNameExistsError as e:
            abort(409, message=str(e))

        return make_response(
            "sub category created",
            SubCategoryResponseSchema().dump(sub_category),
            201,
        )


@sub_categories_blp.route("/<int:sub_category_id>")
class SubCategoryDetail(MethodView):
    def get(self, sub_category_id):
        try:
            sub_category = SubCategoryService.get_by_id(sub_category_id)
        except SubCategoryNotFoundError as e:
            abort(404, message=str(e))

        return make_response(
            "success get sub category",
            SubCategoryDetailResponseSchema().dump(sub_category),
        )

    @sub_categories_blp.arguments(UpdateSubCategorySchema)
    @roles_required("seller", "admin")
    def put(self, validated_data, sub_category_id):
        try:
            sub_category = SubCategoryService.update(sub_category_id, validated_data)
        except SubCategoryNotFoundError as e:
            abort(404, message=str(e))
        except CategoryNotFoundError as e:
            abort(404, message=str(e))
        except SubCategoryNameExistsError as e:
            abort(409, message=str(e))

        return make_response(
            "success update sub category",
            SubCategoryResponseSchema().dump(sub_category),
        )

    @roles_required("seller", "admin")
    def delete(self, sub_category_id):
        try:
            SubCategoryService.delete(sub_category_id)
        except SubCategoryNotFoundError as e:
            abort(404, message=str(e))

        return make_response("success delete sub category")


@sub_categories_blp.route("/products")
class SubCategoryListWithProducts(MethodView):
    @sub_categories_blp.arguments(SubCategoryQuerySchema, location="query")
    def get(self, query_params):
        """List active sub-categories, each with its active products nested.

        Paginated at the sub-category level (mirrors GET /sub-categories/);
        each sub-category's products are returned in full (active only).
        """
        filters = {
            "name": query_params.get("name"),
            "category_id": query_params.get("category_id"),
        }

        paginated = SubCategoryService.get_all_with_products(
            filters=filters,
            sort_by=query_params["sort_by"],
            order=query_params["order"],
            page=query_params["page"],
            limit=query_params["limit"],
        )

        return make_response(
            "get all sub categories with products success",
            SubCategoryWithProductsSchema(many=True).dump(paginated.items),
            pagination=paginate_meta(paginated),
        )
