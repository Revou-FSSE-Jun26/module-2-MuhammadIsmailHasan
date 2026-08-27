from app.routes.users import users_bp
from app.routes.categories import categories_bp
from app.routes.auth import auth_bp
from app.routes.orders import orders_bp


def register_routes(flask_app):
    """Register legacy (non-smorest) blueprints."""
    flask_app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    flask_app.register_blueprint(categories_bp, url_prefix='/api/v1/categories')
    flask_app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    flask_app.register_blueprint(orders_bp, url_prefix='/api/v1/orders')
