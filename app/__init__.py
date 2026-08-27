import os
from flask import Flask

from app.extensions import db, jwt, migrate, api
from app.errors import register_error_handlers
from config import config_by_name


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    flask_app = Flask(__name__)
    flask_app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(flask_app)
    jwt.init_app(flask_app)
    migrate.init_app(flask_app, db)
    api.init_app(flask_app)

    # Flasgger — only if SWAGGER_CONFIG is present (development only)
    swagger_config = flask_app.config.get('SWAGGER_CONFIG')
    if swagger_config:
        from flasgger import Flasgger
        Flasgger(flask_app, config=swagger_config)

    # Register smorest blueprints
    from app.routes.products import products_blp
    from app.routes.users import users_blp
    from app.routes.auth import auth_blp
    from app.routes.categories import categories_blp
    from app.routes.orders import orders_blp
    api.register_blueprint(products_blp)
    api.register_blueprint(users_blp)
    api.register_blueprint(auth_blp)
    api.register_blueprint(categories_blp)
    api.register_blueprint(orders_blp)

    # Error handlers
    register_error_handlers(flask_app)

    return flask_app
