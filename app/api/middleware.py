# app/api/middleware.py
from flask import jsonify
from app.core.shared.exceptions import DomainError, HostingError, ValidationError

def register_error_handlers(app):
    @app.errorhandler(DomainError)
    def handle_domain_error(error):
        return jsonify({
            "success": False,
            "error": "Domain operation failed",
            "message": str(error)
        }), 400
    
    @app.errorhandler(HostingError)
    def handle_hosting_error(error):
        return jsonify({
            "success": False, 
            "error": "Hosting operation failed",
            "message": str(error)
        }), 400
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return jsonify({
            "success": False,
            "error": "Validation failed", 
            "message": str(error)
        }), 400
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({
            "success": False,
            "error": "Endpoint not found"
        }), 404
    
    @app.errorhandler(500)
    def handle_server_error(error):
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500