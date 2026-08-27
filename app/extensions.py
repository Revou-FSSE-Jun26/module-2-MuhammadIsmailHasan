"""
Centralized extension instances.

Extensions are created here WITHOUT an app instance.
They get bound to the app inside create_app() via .init_app(app).
"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_smorest import Api

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
api = Api()
