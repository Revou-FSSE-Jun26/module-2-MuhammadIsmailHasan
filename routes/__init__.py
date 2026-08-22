from routes.users import user_bp
from routes.products import products_bp


def register_routes(app):
    app.register_blueprint(user_bp, url_prefix='/api/v1/users')
    app.register_blueprint(products_bp, url_prefix='/api/v1/products')
