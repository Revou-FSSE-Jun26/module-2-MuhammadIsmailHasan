import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
SQLALCHEMY_TRACK_MODIFICATIONS = False

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
}
