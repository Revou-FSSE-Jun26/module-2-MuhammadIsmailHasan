"""
Application Factory.

create_app() builds and configures a Flask application instance.
This is the entry point for the entire app/ package.
"""

import os
from flask import Flask

from app.extensions import db, jwt, migrate, api
from app.errors import register_error_handlers
from config import config_by_name


def create_app(config_name=None):
    """
    Application factory function.

    Args:
        config_name (str): 'development' or 'production'.
                           Defaults to FLASK_ENV env var or 'development'.

    Returns:
        Flask app instance, fully configured and ready to run.
    """
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

    # Register legacy blueprints (non-smorest routes)
    from app.routes import register_routes
    register_routes(flask_app)

    # Register smorest blueprints
    from app.routes.products import products_blp
    from app.routes.users import users_blp
    from app.routes.auth import auth_blp
    from app.routes.categories import categories_blp
    api.register_blueprint(products_blp)
    api.register_blueprint(users_blp)
    api.register_blueprint(auth_blp)
    api.register_blueprint(categories_blp)

    # Error handlers
    register_error_handlers(flask_app)

    return flask_app
