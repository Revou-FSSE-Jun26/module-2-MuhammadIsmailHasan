"""
Development configuration.

Enables debug mode and SQL echo. API docs are served by flask-smorest.
"""

from config.base import BaseConfig


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    LOG_LEVEL = 'DEBUG'
