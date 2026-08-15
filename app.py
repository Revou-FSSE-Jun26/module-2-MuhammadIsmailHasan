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

    print("Flask app initialized successfully.")
    return app

app = init_app()