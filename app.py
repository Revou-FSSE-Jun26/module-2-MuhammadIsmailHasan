from flask import Flask, jsonify
from utils import db
from dotenv import load_dotenv
from flask_migrate import Migrate
from models.category import Category
from models.product import Product
from models.user import User
from models.order import Order
import os

load_dotenv()

def init_app():
    print("Initializing Flask app...")
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv("DATABASE_TRACK_MODIFICATION")

    db.init_app(app)
    migrate = Migrate(app, db)
    
    return app

app = init_app()