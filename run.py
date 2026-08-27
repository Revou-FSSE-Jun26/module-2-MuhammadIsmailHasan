"""
Entry point for running the application.

Usage:
    python run.py                          -> runs with FLASK_ENV (default: development)
    FLASK_ENV=production python run.py     -> runs with production config
    flask run                              -> Flask CLI picks up create_app from app/
"""

from app import create_app

application = create_app()

if __name__ == '__main__':
    application.run()
