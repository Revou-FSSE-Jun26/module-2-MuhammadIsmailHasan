"""
Development configuration.

Enables debug mode and SQL echo. API docs are served by flask-smorest.
"""

import os

from config.base import BaseConfig

DEFAULT_DEV_ORIGINS = 'http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173'


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    LOG_LEVEL = 'DEBUG'
    CORS_ORIGINS = [
        origin.strip()
        for origin in (os.getenv('CORS_ORIGINS') or DEFAULT_DEV_ORIGINS).split(',')
        if origin.strip()
    ]
