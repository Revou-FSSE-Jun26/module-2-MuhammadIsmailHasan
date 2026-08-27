"""
Production configuration.

Debug off, no SQL echo, shorter token lifetime.
No Flasgger — only flask-smorest OpenAPI docs in production.
"""

import os
from datetime import timedelta
from config.base import BaseConfig


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_ECHO = False

    # Stricter token expiration in production
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '15')))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '7')))

    # No Flasgger in production
    SWAGGER_CONFIG = None
