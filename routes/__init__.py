from routes.users import users_bp
from routes.products import products_bp
from routes.categories import categories_bp
from routes.auth import auth_bp
from routes.orders import orders_bp


def register_routes(app):
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(products_bp, url_prefix='/api/v1/products')
    app.register_blueprint(categories_bp, url_prefix='/api/v1/categories')
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(orders_bp, url_prefix='/api/v1/orders')
