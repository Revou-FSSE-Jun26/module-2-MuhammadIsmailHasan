from routes.users import user_bp
from routes.products import products_bp
from routes.categories import category_bp

def register_routes(app):
    app.register_blueprint(user_bp, url_prefix='/api/v1/users')
    app.register_blueprint(products_bp, url_prefix='/api/v1/products')
    app.register_blueprint(category_bp, url_prefix='/api/v1/categories')
