from flask.views import MethodView
from flask_smorest import Blueprint
from flask import jsonify
from sqlalchemy import text

from app.extensions import db

health_blp = Blueprint(
    'health',
    __name__,
    url_prefix='/api/v1/health',
    description='Health check',
)


@health_blp.route('')
class HealthCheck(MethodView):

    def get(self):
        database_ok = True
        try:
            db.session.execute(text('SELECT 1'))
        except Exception:
            database_ok = False
            db.session.rollback()

        status_code = 200 if database_ok else 503

        return jsonify({
            'status': database_ok,
            'message': 'healthy' if database_ok else 'unhealthy',
            'data': {
                'database': 'up' if database_ok else 'down',
            },
        }), status_code
