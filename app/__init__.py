import os
from flask import Flask

from app.extensions import db, jwt, migrate, api
from app.errors import register_error_handlers
from app.logging_config import configure_logging
from config import config_by_name


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    flask_app = Flask(__name__)
    flask_app.config.from_object(config_by_name[config_name])

    # Logging
    configure_logging(flask_app)

    # Initialize extensions
    db.init_app(flask_app)
    jwt.init_app(flask_app)
    migrate.init_app(flask_app, db)
    api.init_app(flask_app)
    api.spec.components.security_scheme(
        'BearerAuth',
        {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'Paste the access_token returned by /api/v1/auth/login',
        },
    )
    api.spec.options['security'] = [{'BearerAuth': []}]

    # Register smorest blueprints
    from app.routes.products import products_blp
    from app.routes.product_images import product_images_blp
    from app.routes.users import users_blp
    from app.routes.auth import auth_blp
    from app.routes.categories import categories_blp
    from app.routes.orders import orders_blp
    from app.routes.carts import cart_blp
    from app.routes.user_profiles import profile_blp
    from app.routes.user_addresses import addresses_blp
    from app.routes.health import health_blp
    api.register_blueprint(products_blp)
    api.register_blueprint(product_images_blp)
    api.register_blueprint(users_blp)
    api.register_blueprint(auth_blp)
    api.register_blueprint(categories_blp)
    api.register_blueprint(orders_blp)
    api.register_blueprint(cart_blp)
    api.register_blueprint(profile_blp)
    api.register_blueprint(addresses_blp)
    api.register_blueprint(health_blp)

    # Error handlers
    register_error_handlers(flask_app)

    flask_app.logger.info('application initialized (env=%s)', config_name)

    return flask_app
