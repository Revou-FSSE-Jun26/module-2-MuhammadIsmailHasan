from flask import jsonify

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "message" : "resource not found",
            "status": False
        }), 404
        
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "message" : "method not allowed",
            "status" : False
        }), 405
        
    @app.errorhandler(500) 
    def internal_error(error):
        return jsonify({
            "message" : "internal server error",
            "status": False
        }), 500