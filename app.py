from flask import Flask
from flasgger import Flasgger
from flask_migrate import Migrate
from helper.utils import db
from config import SWAGGER_CONFIG
from models import User, Product, Category, Order
from routes import register_routes
from errors import register_error_handlers
from flask_jwt_extended import JWTManager

def init_app():
    app = Flask(__name__)
    app.config.from_object('config')

    db.init_app(app)
    Migrate(app, db)
    jwt = JWTManager(app)
    Flasgger(app, config=SWAGGER_CONFIG)

    register_routes(app)
    register_error_handlers(app)

    return app


app = init_app()
