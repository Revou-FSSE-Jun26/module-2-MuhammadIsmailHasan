"""
Configuration package.

Usage:
    from config import config_by_name

    app.config.from_object(config_by_name['development'])
    app.config.from_object(config_by_name['production'])
"""

from config.base import BaseConfig
from config.development import DevelopmentConfig
from config.production import ProductionConfig

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
