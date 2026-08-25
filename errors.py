from flask import jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, DataError
from helper.utils import db


def register_error_handlers(app):

    # ─── HTTP Error Handlers ───

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'message': 'bad request',
            'status': False
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'message': 'missing or invalid authentication token',
            'status': False
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'message': "you don't have permission to access this resource",
            'status': False
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'message': 'resource not found',
            'status': False
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'message': 'method not allowed',
            'status': False
        }), 405

    @app.errorhandler(409)
    def conflict(error):
        return jsonify({
            'message': 'resource conflict',
            'status': False
        }), 409

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'message': 'internal server error',
            'status': False
        }), 500

    # ─── SQLAlchemy Error Handlers ───

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        db.session.rollback()
        current_app.logger.error('integrity error: %s', error)
        return jsonify({
            'message': 'data integrity violation',
            'status': False
        }), 422

    @app.errorhandler(DataError)
    def handle_data_error(error):
        db.session.rollback()
        current_app.logger.error('data error: %s', error)
        return jsonify({
            'message': 'invalid data format',
            'status': False
        }), 422

    @app.errorhandler(OperationalError)
    def handle_operational_error(error):
        db.session.rollback()
        current_app.logger.error('operational error: %s', error)
        return jsonify({
            'message': 'database connection issue',
            'status': False
        }), 503

    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        db.session.rollback()
        current_app.logger.error('database error: %s', error)
        return jsonify({
            'message': 'internal server error',
            'status': False
        }), 500
