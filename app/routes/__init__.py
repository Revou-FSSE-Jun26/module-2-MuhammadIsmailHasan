from app.routes.categories import categories_bp
from app.routes.orders import orders_bp


def register_routes(flask_app):
    flask_app.register_blueprint(categories_bp, url_prefix='/api/v1/categories')
    flask_app.register_blueprint(orders_bp, url_prefix='/api/v1/orders')
