from flask import Flask, jsonify
from flasgger import Flasgger
from utils import db
from dotenv import load_dotenv
from flask_migrate import Migrate
from models.category import Category
from models.product import Product
from models.user import User
from models.order import Order
from routes.users import user_bp
from routes.products import products_bp
import os

load_dotenv()

def init_app():
    print("Initializing Flask app...")
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv("DATABASE_TRACK_MODIFICATION")

    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Configure Flasgger
    Flasgger(app, config={
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
        'description': 'E-commerce API for learning Flask and SQLAlchemy'
    })
    
    app.register_blueprint(user_bp)
    app.register_blueprint(products_bp)
    
    return app

app = init_app()