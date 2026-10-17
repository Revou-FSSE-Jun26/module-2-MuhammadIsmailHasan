"""
Base configuration shared across all environments.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    # ─── Database ─────────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ─── JWT ──────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'super-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '1')))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '30')))

    # ─── flask-smorest (OpenAPI) ──────────────────────────────────────────────
    API_TITLE = 'Revoshop API'
    API_VERSION = 'v1'
    OPENAPI_VERSION = '3.0.3'
    OPENAPI_URL_PREFIX = '/docs'
    OPENAPI_SWAGGER_UI_PATH = '/swagger-ui'
    OPENAPI_SWAGGER_UI_URL = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'

    # ─── Midtrans (payment gateway) ───────────────────────────────────────────
    MIDTRANS_SERVER_KEY = os.getenv('MIDTRANS_SERVER_KEY', '')
    MIDTRANS_CLIENT_KEY = os.getenv('MIDTRANS_CLIENT_KEY', '')
    MIDTRANS_IS_PRODUCTION = os.getenv('MIDTRANS_IS_PRODUCTION', 'false').lower() == 'true'
    MIDTRANS_EXPIRY_MINUTES = int(os.getenv('MIDTRANS_EXPIRY_MINUTES', '1440'))

    # ─── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv('CORS_ORIGINS', '').split(',')
        if origin.strip()
    ]

    # ─── Product images ───────────────────────────────────────────────────────
    IMAGE_BASE_URL = os.getenv('IMAGE_BASE_URL') or '/static/images'

    # ─── Image upload (S3) ────────────────────────────────────────────────────
    AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET', '')
    AWS_S3_REGION = os.getenv('AWS_S3_REGION') or 'ap-southeast-1'
    MAX_IMAGE_UPLOAD_BYTES = int(os.getenv('MAX_IMAGE_UPLOAD_BYTES') or 5 * 1024 * 1024)
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH') or 6 * 1024 * 1024)

    # ─── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'true').lower() == 'true'
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    # Daily rotation: a new file is started at midnight; keep this many days.
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '30'))
