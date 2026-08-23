from flask import jsonify

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "message": "bad request",
            "status": False
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            "message": "missing or invalid authentication token",
            "status": False
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            "message": "you don't have permission to access this resource",
            "status": False
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "message": "resource not found",
            "status": False
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "message": "method not allowed",
            "status": False
        }), 405

    @app.errorhandler(409)
    def conflict(error):
        return jsonify({
            "message": "resource conflict",
            "status": False
        }), 409

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "message": "internal server error",
            "status": False
        }), 500