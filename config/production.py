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
    LOG_LEVEL = "INFO"
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "false").lower() == "true"

    @classmethod
    def validate(cls, config):
        # Load the shared env-driven config first, then apply prod-only rules.
        super().validate(config)

        # Stricter token expiration in production.
        config.from_mapping(
            JWT_ACCESS_TOKEN_EXPIRES=timedelta(
                minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "15"))
            ),
            JWT_REFRESH_TOKEN_EXPIRES=timedelta(
                days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "7"))
            ),
        )

        problems = []
        if not config.get("SQLALCHEMY_DATABASE_URI"):
            problems.append("DATABASE_URL is not set")
        if len(config.get("JWT_SECRET_KEY") or "") < 32:
            problems.append(
                "JWT_SECRET_KEY must be set to at least 32 random characters"
            )
        if problems:
            raise RuntimeError(
                "Invalid production configuration: " + "; ".join(problems)
            )
