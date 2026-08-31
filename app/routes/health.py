from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy import text

from app.extensions import db
from app.utils.http import make_response

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

        return make_response(
            'healthy' if database_ok else 'unhealthy',
            {'database': 'up' if database_ok else 'down'},
            status_code=200 if database_ok else 503,
            status=database_ok,
        )
