"""
Development configuration.

Enables debug mode, SQL echo, and Flasgger (legacy Swagger docs).
Flasgger will be removed once all routes migrate to flask-smorest.
"""

import os
from config.base import BaseConfig


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ECHO = True

    # ─── Flasgger (legacy — temporary until full smorest migration) ───────────
    SWAGGER_CONFIG = {
        'headers': [],
        'specs': [
            {
                'endpoint': 'apispec_1',
                'route': '/apispec_1.json',
                'rule_filter': lambda rule: True,
                'model_filter': lambda tag: True,
            }
        ],
        'static_url_path': '/flasgger_static',
        'swagger_ui': True,
        'specs_route': '/apidocs/',
        'title': 'Revoshop API',
        'version': '1.0.0',
        'description': 'E-commerce API v1 for learning Flask and SQLAlchemy',
        'host': os.getenv('API_HOST', 'localhost:5000'),
        'basePath': '/',
        'schemes': ['http', 'https'],
        'securityDefinitions': {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': 'JWT token. Format: Bearer <access_token>'
            }
        },
    }
