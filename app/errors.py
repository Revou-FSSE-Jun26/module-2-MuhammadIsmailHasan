from flask import jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, DataError

from app.extensions import db


def register_error_handlers(flask_app):

    # ─── HTTP Error Handlers ───

    @flask_app.errorhandler(400)
    def bad_request(error):
        # flask-smorest abort() passes message via error.data
        message = 'bad request'
        if hasattr(error, 'data') and 'message' in error.data:
            message = error.data['message']
        return jsonify({
            'message': message,
            'status': False
        }), 400

    @flask_app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'message': 'missing or invalid authentication token',
            'status': False
        }), 401

    @flask_app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'message': "you don't have permission to access this resource",
            'status': False
        }), 403

    @flask_app.errorhandler(404)
    def not_found(error):
        message = 'resource not found'
        if hasattr(error, 'data') and 'message' in error.data:
            message = error.data['message']
        return jsonify({
            'message': message,
            'status': False
        }), 404

    @flask_app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'message': 'method not allowed',
            'status': False
        }), 405

    @flask_app.errorhandler(409)
    def conflict(error):
        return jsonify({
            'message': 'resource conflict',
            'status': False
        }), 409

    @flask_app.errorhandler(422)
    def unprocessable_entity(error):
        # flask-smorest validation errors come as 422 with structured data
        if hasattr(error, 'data') and 'messages' in error.data:
            messages = error.data['messages']
            # Extract first error message for flat API response
            if 'json' in messages:
                for field, field_messages in messages['json'].items():
                    if isinstance(field_messages, list) and field_messages:
                        return jsonify({
                            'message': field_messages[0],
                            'status': False
                        }), 422
            if 'query' in messages:
                for field, field_messages in messages['query'].items():
                    if isinstance(field_messages, list) and field_messages:
                        return jsonify({
                            'message': field_messages[0],
                            'status': False
                        }), 422
            return jsonify({
                'message': 'validation error',
                'status': False
            }), 422

        return jsonify({
            'message': 'data integrity violation',
            'status': False
        }), 422

    @flask_app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'message': 'internal server error',
            'status': False
        }), 500

    # ─── SQLAlchemy Error Handlers ───

    @flask_app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        db.session.rollback()
        current_app.logger.error('integrity error: %s', error)
        return jsonify({
            'message': 'data integrity violation',
            'status': False
        }), 422

    @flask_app.errorhandler(DataError)
    def handle_data_error(error):
        db.session.rollback()
        current_app.logger.error('data error: %s', error)
        return jsonify({
            'message': 'invalid data format',
            'status': False
        }), 422

    @flask_app.errorhandler(OperationalError)
    def handle_operational_error(error):
        db.session.rollback()
        current_app.logger.error('operational error: %s', error)
        return jsonify({
            'message': 'database connection issue',
            'status': False
        }), 503

    @flask_app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        db.session.rollback()
        current_app.logger.error('database error: %s', error)
        return jsonify({
            'message': 'internal server error',
            'status': False
        }), 500
