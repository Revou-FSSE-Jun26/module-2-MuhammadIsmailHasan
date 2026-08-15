from flask import Flask, jsonify
from utils import db
import os
from dotenv import load_dotenv

load_dotenv()

def init_app():
    print("Initializing Flask app...")
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv("DATABASE_TRACK_MODIFICATION")

    db.init_app(app)

    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
        except Exception as e:
            print(f"Error creating tables: {e}")

    return app

app = init_app()