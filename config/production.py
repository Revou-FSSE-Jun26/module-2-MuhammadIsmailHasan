"""
Production configuration.

Debug off, no SQL echo, shorter token lifetime.
API docs are served by flask-smorest.
"""

import os
from datetime import timedelta
from config.base import BaseConfig


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    LOG_LEVEL = 'INFO'

    # Stricter token expiration in production
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '15')))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '7')))
